#!/usr/bin/env python3
"""
Targon 注册机【Cloudflare 版】
使用 Cloudflare Email Routing 和 IMAP 读取邮件
"""

import json
import time
import random
import string
import re
import uuid
import httpx
import pyotp
import imaplib
import email
from email.header import decode_header
from bs4 import BeautifulSoup
from datetime import datetime

class TargonCloudflare:
    def __init__(self):
        self.visitor_id = str(uuid.uuid4())
        self.email_address = None
        self.session_cookie = None
        self.keys_file = "api_keys.txt"
        self.config = self.load_config()

        # HTTP客户端配置
        self.client = httpx.Client(
            timeout=60.0,
            headers={
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36',
                'Accept': '*/*',
                'Accept-Language': 'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7',
                'sec-ch-ua': '"Not)A;Brand";v="8", "Chromium";v="138", "Google Chrome";v="138"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"macOS"',
                'sec-fetch-dest': 'empty',
                'sec-fetch-mode': 'cors',
                'sec-fetch-site': 'same-origin',
                'sec-gpc': '1',
                'visitor-id': self.visitor_id
            }
        )

    def load_config(self):
        """加载配置文件"""
        try:
            with open('config.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print("❌ 错误: 配置文件 'config.json' 未找到。")
            print("请将 'config.json.example' 复制为 'config.json' 并填入您的配置。")
            exit(1)
        except json.JSONDecodeError:
            print("❌ 错误: 配置文件 'config.json' 格式不正确。")
            exit(1)

    def generate_password(self):
        """生成随机密码"""
        length = 12
        chars = string.ascii_letters + string.digits + "!@#$%^&*"
        return ''.join(random.choice(chars) for _ in range(length))

    def get_email_address(self):
        """生成基于域名的随机邮箱地址"""
        if not self.config.get('domain'):
            print("❌ 错误: 域名未在 'config.json' 中配置。")
            return False
        
        random_part = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
        self.email_address = f"{random_part}@{self.config['domain']}"
        print(f"📧 生成邮箱地址: {self.email_address}")
        return True

    def register_account(self, password):
        """注册Targon账户"""
        try:
            print("🚀 开始注册账户...")
            
            register_data = {
                "0": {
                    "json": {
                        "email": self.email_address,
                        "password": password,
                        "password2": password
                    }
                }
            }
            
            response = self.client.post(
                "https://targon.com/api/trpc/account.createAccount?batch=1",
                json=register_data,
                headers={
                    'Content-Type': 'application/json',
                    'x-trpc-source': 'react'
                }
            )
            
            if response.status_code == 200:
                print("✅ 账户注册成功")
                return True
            else:
                print(f"❌ 注册失败: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ 注册异常: {e}")
            return False

    def get_activation_link_from_imap(self, max_attempts=15, delay=10):
        """通过IMAP获取激活链接"""
        try:
            print("📬 通过 IMAP 等待激活邮件...")
            
            for attempt in range(max_attempts):
                print(f"📧 检查邮件 (第 {attempt + 1}/{max_attempts} 次)...")
                
                try:
                    mail = imaplib.IMAP4_SSL(self.config['imap_server'])
                    mail.login(self.config['imap_user'], self.config['imap_password'])
                    mail.select('inbox')
                    
                    # 搜索发给临时邮箱的、来自Targon的未读邮件
                    search_criteria = f'(UNSEEN TO "{self.email_address}" FROM "noreply@manifold.inc")'
                    status, messages = mail.search(None, search_criteria)

                    if status == 'OK' and messages[0]:
                        for num in messages[0].split():
                            status, data = mail.fetch(num, '(RFC822)')
                            if status == 'OK':
                                msg = email.message_from_bytes(data[0][1])
                                subject = decode_header(msg['subject'])[0][0]
                                if isinstance(subject, bytes):
                                    subject = subject.decode()

                                if 'Targon' in subject:
                                    print("🎯 找到Targon验证邮件!")
                                    
                                    body = ""
                                    if msg.is_multipart():
                                        for part in msg.walk():
                                            ctype = part.get_content_type()
                                            if ctype == "text/html":
                                                body = part.get_payload(decode=True).decode()
                                                break
                                    else:
                                        body = msg.get_payload(decode=True).decode()
                                    
                                    if body:
                                        soup = BeautifulSoup(body, 'html.parser')
                                        links = soup.find_all('a', href=True)
                                        for link in links:
                                            href = link['href']
                                            if 'email-verification' in href and 'token=' in href:
                                                print("🔗 成功提取激活链接")
                                                mail.logout()
                                                return href
                    
                    mail.logout()

                except imaplib.IMAP4.error as e:
                    print(f"❌ IMAP 登录或读取失败: {e}")
                    # 如果登录失败，等待更长时间可能没有帮助，提前退出
                    return None
                except Exception as e:
                    print(f"❌ 检查邮件时发生未知错误: {e}")


                if attempt < max_attempts - 1:
                    print(f"⏰ 等待 {delay} 秒后重试...")
                    time.sleep(delay)
            
            print("❌ 未能获取到激活链接")
            return None
            
        except Exception as e:
            print(f"❌ 获取激活链接异常: {e}")
            return None

    def activate_email(self, activation_link):
        """激活邮箱"""
        try:
            print("🔗 开始激活邮箱...")
            
            activation_headers = {
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                'Accept-Language': 'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7',
                'sec-fetch-dest': 'document',
                'sec-fetch-mode': 'navigate',
                'sec-fetch-site': 'none',
                'sec-fetch-user': '?1',
                'upgrade-insecure-requests': '1',
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36'
            }
            
            current_url = activation_link
            max_redirects = 5
            redirect_count = 0
            
            while redirect_count < max_redirects:
                response = self.client.get(current_url, headers=activation_headers, follow_redirects=False)
                
                set_cookie_headers = response.headers.get_list('set-cookie')
                for set_cookie in set_cookie_headers:
                    if 'auth_session=' in set_cookie:
                        parts = set_cookie.split(';')
                        for part in parts:
                            if part.strip().startswith('auth_session='):
                                self.session_cookie = part.strip().split('=', 1)[1]
                                print("🍪 获取到登录凭证")
                                break
                
                if response.status_code in [301, 302, 307, 308]:
                    location = response.headers.get('Location')
                    if not location: break
                    
                    if location.startswith('/'):
                        from urllib.parse import urljoin
                        current_url = urljoin('https://targon.com', location)
                    else:
                        current_url = location
                    
                    redirect_count += 1
                    continue
                
                elif response.status_code == 200:
                    print("✅ 邮箱激活成功")
                    return True
                else:
                    print(f"❌ 激活失败: {response.status_code}")
                    return False
            
            print("❌ 重定向次数过多")
            return False
            
        except Exception as e:
            print(f"❌ 激活异常: {e}")
            return False

    def setup_2fa(self):
        """设置2FA"""
        try:
            if not self.session_cookie:
                print("❌ 没有有效的登录凭证")
                return False
            
            print("🔐 开始设置2FA...")
            
            headers = {
                'Content-Type': 'application/json',
                'x-trpc-source': 'react',
                'Referer': 'https://targon.com/two-factor-auth'
            }
            cookies = {'auth_session': self.session_cookie}
            
            response = self.client.get(
                "https://targon.com/api/trpc/account.createTwoFactorURI?batch=1&input=%7B%220%22%3A%7B%22json%22%3Anull%2C%22meta%22%3A%7B%22values%22%3A%5B%22undefined%22%5D%7D%7D%7D",
                headers=headers,
                cookies=cookies
            )
            
            if response.status_code != 200:
                print(f"❌ 创建2FA失败: {response.status_code}")
                return False
            
            response_data = response.json()
            result_data = response_data[0]['result']['data']['json']
            two_factor_secret = result_data['twoFactorSecret']
            manual_code = result_data['manualCode']
            
            totp = pyotp.TOTP(manual_code)
            otp_code = totp.now()
            
            enable_data = {
                "0": {
                    "json": {
                        "otp": otp_code,
                        "twoFactorSecret": two_factor_secret
                    }
                }
            }
            
            response = self.client.post(
                "https://targon.com/api/trpc/account.enable2FA?batch=1",
                json=enable_data,
                headers=headers,
                cookies=cookies
            )
            
            if response.status_code == 200:
                print("✅ 2FA设置成功")
                return True
            else:
                print(f"❌ 启用2FA失败: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ 2FA设置异常: {e}")
            return False

    def get_api_keys(self):
        """获取API密钥"""
        try:
            if not self.session_cookie:
                print("❌ 没有有效的登录凭证")
                return []
            
            print("🔑 获取API密钥...")
            
            headers = {
                'x-trpc-source': 'react',
                'Referer': 'https://targon.com/settings'
            }
            cookies = {'auth_session': self.session_cookie}
            
            query_url = f"https://targon.com/api/trpc/keys.getApiKeys,model.getPopularModels,account.getUserBookmarks,account.getUserInterest,account.getUserSubscription,account.check2FA,account.getTaoPrice,account.getAlphaPrice,notification.getNotifications?batch=1&input=%7B%220%22%3A%7B%22json%22%3Anull%2C%22meta%22%3A%7B%22values%22%3A%5B%22undefined%22%5D%7D%7D%2C%221%22%3A%7B%22json%22%3A%7B%22days%22%3A30%2C%22limit%22%3A3%7D%7D%2C%222%22%3A%7B%22json%22%3Anull%2C%22meta%22%3A%7B%22values%22%3A%5B%22undefined%22%5D%7D%7D%2C%223%22%3A%7B%22json%22%3Anull%2C%22meta%22%3A%7B%22values%22%3A%5B%22undefined%22%5D%7D%7D%2C%224%22%3A%7B%22json%22%3Anull%2C%22meta%22%3A%7B%22values%22%3A%5B%22undefined%22%5D%7D%7D%2C%225%22%3A%7B%22json%22%3A%7B%22email%22%3A%22{self.email_address}%22%7D%7D%2C%226%22%3A%7B%22json%22%3Anull%2C%22meta%22%3A%7B%22values%22%3A%5B%22undefined%22%5D%7D%7D%2C%227%22%3A%7B%22json%22%3Anull%2C%22meta%22%3A%7B%22values%22%3A%5B%22undefined%22%5D%7D%7D%2C%228%22%3A%7B%22json%22%3Anull%2C%22meta%22%3A%7B%22values%22%3A%5B%22undefined%22%5D%7D%7D%7D"
            
            response = self.client.get(query_url, headers=headers, cookies=cookies)
            
            if response.status_code == 200:
                response_data = response.json()
                api_keys_data = response_data[0]['result']['data']['json']
                
                if api_keys_data:
                    print(f"✅ 获取到 {len(api_keys_data)} 个API密钥")
                    return api_keys_data
                else:
                    print("⚠️ 未找到API密钥")
                    return []
            else:
                print(f"❌ 获取密钥失败: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"❌ 获取密钥异常: {e}")
            return []

    def save_keys(self, api_keys):
        """保存API密钥到文件"""
        try:
            existing_keys = set()
            try:
                with open(self.keys_file, 'r', encoding='utf-8') as f:
                    existing_keys = {line.strip() for line in f if line.strip()}
            except FileNotFoundError:
                pass
            
            new_keys = []
            for key_info in api_keys:
                key = key_info.get('key')
                if key and key not in existing_keys:
                    new_keys.append(key)
            
            if new_keys:
                with open(self.keys_file, 'a', encoding='utf-8') as f:
                    for key in new_keys:
                        f.write(key + '\n')
                print(f"💾 保存了 {len(new_keys)} 个新密钥到 {self.keys_file}")
            else:
                print("ℹ️ 没有新密钥需要保存")
                
        except Exception as e:
            print(f"❌ 保存密钥异常: {e}")

    def register_single_account(self):
        """注册单个账户的完整流程"""
        try:
            print(f"\n🎯 开始注册新账户 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            if not self.get_email_address(): return False
            
            password = self.generate_password()
            print(f"🔐 生成密码: {password}")
            
            if not self.register_account(password): return False
            
            activation_link = self.get_activation_link_from_imap()
            if not activation_link: return False
            
            if not self.activate_email(activation_link): return False
            
            if not self.setup_2fa(): return False
            
            api_keys = self.get_api_keys()
            if not api_keys:
                print("❌ 未获取到API密钥")
                return False
            
            self.save_keys(api_keys)
            
            print("\n🎉 账户注册完成!")
            print(f"📧 邮箱: {self.email_address}")
            print(f"🔐 密码: {password}")
            print(f"🔑 API密钥:")
            for key_info in api_keys:
                key = key_info.get('key', '')
                print(f"   {key[:15]}...{key[-8:] if len(key) > 23 else key}")
            
            return True
            
        except Exception as e:
            print(f"❌ 注册流程异常: {e}")
            return False

    def run_batch(self, count=1):
        """批量注册"""
        print(f"📦 开始批量注册 {count} 个账户")
        
        success_count = 0
        for i in range(count):
            print(f"\n{'='*50}")
            print(f"📋 注册进度: {i+1}/{count}")
            
            bot = TargonCloudflare()
            if bot.register_single_account():
                success_count += 1
            
            if i < count - 1:
                wait_time = 5
                print(f"⏳ 等待 {wait_time} 秒后继续...")
                time.sleep(wait_time)
        
        print(f"\n🏆 批量注册完成!")
        print(f"✅ 成功注册: {success_count}/{count}")
        
        try:
            with open(self.keys_file, 'r', encoding='utf-8') as f:
                total_keys = len([line.strip() for line in f if line.strip()])
            print(f"📊 总密钥数: {total_keys}")
        except FileNotFoundError:
            print("📊 总密钥数: 0")

    def __del__(self):
        """清理资源"""
        try:
            self.client.close()
        except:
            pass

def show_logo():
    """显示程序logo"""
    logo = """
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║  ████████╗ █████╗ ██████╗  ██████╗  ██████╗ ███╗   ██╗       ║
║  ╚══██╔══╝██╔══██╗██╔══██╗██╔════╝ ██╔═══██╗████╗  ██║       ║
║     ██║   ███████║██████╔╝██║  ███╗██║   ██║██╔██╗ ██║       ║
║     ██║   ██╔══██║██╔══██╗██║   ██║██║   ██║██║╚██╗██║       ║
║     ██║   ██║  ██║██║  ██║╚██████╔╝╚██████╔╝██║ ╚████║       ║
║     ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝  ╚═════╝ ╚═╝  ╚═══╝       ║
║                                                              ║
║               🤖 注册机【Cloudflare 版】 🤖                  ║
║           用自己的域名，优雅地躺平，注册得更稳！             ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
    """
    print(logo)

def get_user_choice():
    """获取用户选择"""
    print("\n📋 请选择运行模式：")
    print("   1️⃣  单个账户注册")
    print("   2️⃣  批量账户注册")
    print("   0️⃣  退出程序")
    print("=" * 50)
    
    while True:
        try:
            choice = input("请输入选择 (0/1/2): ").strip()
            if choice in ['0', '1', '2']:
                return int(choice)
            else:
                print("❌ 无效选择，请输入 0、1 或 2")
        except KeyboardInterrupt:
            print("\n\n👋 程序已退出")
            return 0
        except Exception:
            print("❌ 输入错误，请重新输入")

def get_batch_count():
    """获取批量注册数量"""
    print("\n📊 批量注册设置：")
    while True:
        try:
            count = input("请输入注册账户数量 (1-100): ").strip()
            count = int(count)
            if 1 <= count <= 100:
                return count
            else:
                print("❌ 数量必须在 1-100 之间")
        except KeyboardInterrupt:
            print("\n\n👋 程序已退出")
            return 0
        except ValueError:
            print("❌ 请输入有效的数字")
        except Exception:
            print("❌ 输入错误，请重新输入")

def main():
    """主函数"""
    show_logo()
    
    print("🔧 程序版本：v2.0.0 (Cloudflare 版)")
    print("👨‍💻 作者信息：云胡不喜@linux.do")
    print("📧 邮箱方案：Cloudflare Email Routing")
    print("🎯 目标平台：Targon.com")
    
    # 检查配置
    bot = TargonCloudflare()

    while True:
        choice = get_user_choice()
        
        if choice == 0:
            print("\n👋 感谢使用！再见~")
            break
        elif choice == 1:
            print("\n🎯 启动单个账户注册模式...")
            bot.register_single_account()
            
            continue_choice = input("\n🤔 是否继续注册？(y/n): ").strip().lower()
            if continue_choice not in ['y', 'yes', '是']:
                print("\n👋 程序结束，感谢使用！")
                break
                
        elif choice == 2:
            count = get_batch_count()
            if count == 0: break
            
            print(f"\n🚀 启动批量注册模式，目标数量：{count}")
            print("⚠️  批量注册可能需要较长时间，请耐心等待...")
            
            confirm = input(f"确认开始批量注册 {count} 个账户？(y/n): ").strip().lower()
            if confirm in ['y', 'yes', '是']:
                bot.run_batch(count)
            else:
                print("❌ 已取消批量注册")
                
            continue_choice = input("\n🤔 是否继续使用程序？(y/n): ").strip().lower()
            if continue_choice not in ['y', 'yes', '是']:
                print("\n👋 程序结束，感谢使用！")
                break

if __name__ == "__main__":
    main()