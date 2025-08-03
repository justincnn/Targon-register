import httpx
import pyotp
from loguru import logger

class TargonRegistrar:
    def __init__(self):
        self.client = httpx.Client(
            timeout=60.0,
            headers={
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36',
                'Accept': '*/*',
                'Accept-Language': 'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7',
                'Content-Type': 'application/json',
                'sec-ch-ua': '"Not)A;Brand";v="8", "Chromium";v="138", "Google Chrome";v="138"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"macOS"',
                'sec-fetch-dest': 'empty',
                'sec-fetch-mode': 'cors',
                'sec-fetch-site': 'same-origin',
                'x-trpc-source': 'react'
            }
        )
        self.session_cookie = None
    
    def register_account(self, email, password):
        """
        注册Targon账户
        
        Args:
            email: 邮箱地址
            password: 密码
            
        Returns:
            bool: 注册是否成功
        """
        try:
            logger.info(f"开始注册账户: {email}")
            
            # 构造注册请求数据
            register_data = {
                "0": {
                    "json": {
                        "email": email,
                        "password": password,
                        "password2": password
                    }
                }
            }
            
            # 发送注册请求
            response = self.client.post(
                "https://targon.com/api/trpc/account.createAccount?batch=1",
                json=register_data
            )
            
            logger.info(f"注册请求响应状态: {response.status_code}")
            
            if response.status_code == 200:
                logger.info(f"账户注册成功: {email}")
                return True
            else:
                logger.error(f"账户注册失败: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"注册过程中发生错误: {e}")
            return False
    
    def activate_email(self, activation_link):
        """
        激活邮箱
        
        Args:
            activation_link: 激活链接
            
        Returns:
            bool: 激活是否成功
        """
        try:
            logger.info(f"开始激活邮箱: {activation_link}")
            
            # 设置激活请求的headers
            activation_headers = {
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                'Accept-Language': 'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7',
                'sec-ch-ua': '"Not)A;Brand";v="8", "Chromium";v="138", "Google Chrome";v="138"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"macOS"',
                'sec-fetch-dest': 'document',
                'sec-fetch-mode': 'navigate',
                'sec-fetch-site': 'none',
                'sec-fetch-user': '?1',
                'upgrade-insecure-requests': '1',
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36'
            }
            
            # 手动处理重定向以确保获取所有cookie
            current_url = activation_link
            max_redirects = 5
            redirect_count = 0
            
            while redirect_count < max_redirects:
                response = self.client.get(
                    current_url,
                    headers=activation_headers,
                    follow_redirects=False  # 不自动跟随重定向
                )
                
                logger.info(f"请求 {current_url} 响应状态: {response.status_code}")
                
                # 检查Set-Cookie响应头
                set_cookie_headers = response.headers.get_list('set-cookie')
                if set_cookie_headers:
                    logger.info(f"收到Set-Cookie头: {len(set_cookie_headers)}个")
                    for set_cookie in set_cookie_headers:
                        if 'auth_session=' in set_cookie:
                            # 提取auth_session的值
                            parts = set_cookie.split(';')
                            for part in parts:
                                if part.strip().startswith('auth_session='):
                                    self.session_cookie = part.strip().split('=', 1)[1]
                                    logger.info(f"从Set-Cookie头获取到session cookie: {self.session_cookie[:20]}...")
                                    break
                
                # 检查并收集cookie（备用方法）
                try:
                    for cookie in response.cookies:
                        if hasattr(cookie, 'name') and cookie.name == 'auth_session':
                            if not self.session_cookie:  # 如果还没有从Set-Cookie头获取到
                                self.session_cookie = cookie.value
                                logger.info(f"从cookies获取到session cookie: {self.session_cookie[:20]}...")
                except Exception as e:
                    logger.debug(f"检查cookies时出错（这是正常的）: {e}")
                
                # 如果是重定向状态码，获取Location头并继续
                if response.status_code in [301, 302, 307, 308]:
                    location = response.headers.get('Location')
                    if not location:
                        logger.error("重定向响应中没有Location头")
                        break
                    
                    # 处理相对URL
                    if location.startswith('/'):
                        from urllib.parse import urljoin
                        current_url = urljoin('https://targon.com', location)
                    else:
                        current_url = location
                    
                    logger.info(f"重定向到: {current_url}")
                    redirect_count += 1
                    continue
                    
                elif response.status_code == 200:
                    logger.info("激活流程完成")
                    break
                else:
                    logger.error(f"激活失败，状态码: {response.status_code}")
                    return False
            
            if redirect_count >= max_redirects:
                logger.error("重定向次数过多")
                return False
            
            # 检查是否获取到session cookie
            if self.session_cookie:
                logger.info("邮箱激活成功，已获取session")
                return True
            else:
                logger.warning("邮箱激活成功但未获取到session cookie")
                return True
                
        except Exception as e:
            logger.error(f"激活过程中发生错误: {e}")
            return False
    
    def create_2fa(self):
        """
        创建2FA设置
        
        Returns:
            dict: 包含2FA URI和密钥的字典，失败返回None
        """
        try:
            logger.info("开始创建2FA设置")
            
            if not self.session_cookie:
                logger.error("没有有效的session cookie")
                return None
            
            # 设置请求headers和cookies
            headers = self.client.headers.copy()
            headers.update({
                'Referer': 'https://targon.com/two-factor-auth',
                'Origin': 'https://targon.com'
            })
            
            cookies = {'auth_session': self.session_cookie}
            
            # 发送创建2FA请求
            response = self.client.get(
                "https://targon.com/api/trpc/account.createTwoFactorURI?batch=1&input=%7B%220%22%3A%7B%22json%22%3Anull%2C%22meta%22%3A%7B%22values%22%3A%5B%22undefined%22%5D%7D%7D%7D",
                headers=headers,
                cookies=cookies
            )
            
            logger.info(f"创建2FA请求响应状态: {response.status_code}")
            
            if response.status_code == 200:
                response_data = response.json()
                
                if response_data and len(response_data) > 0:
                    result_data = response_data[0].get('result', {}).get('data', {}).get('json', {})
                    
                    if result_data:
                        two_factor_secret = result_data.get('twoFactorSecret')
                        manual_code = result_data.get('manualCode')
                        uri = result_data.get('uri')
                        
                        logger.info(f"2FA创建成功")
                        logger.info(f"Manual Code: {manual_code}")
                        
                        return {
                            'two_factor_secret': two_factor_secret,
                            'manual_code': manual_code,
                            'uri': uri
                        }
                
                logger.error("2FA响应数据格式不正确")
                return None
            else:
                logger.error(f"创建2FA失败: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"创建2FA过程中发生错误: {e}")
            return None
    
    def enable_2fa(self, two_factor_secret, manual_code):
        """
        启用2FA
        
        Args:
            two_factor_secret: 2FA密钥
            manual_code: 手动输入代码
            
        Returns:
            bool: 启用是否成功
        """
        try:
            logger.info("开始启用2FA")
            
            if not self.session_cookie:
                logger.error("没有有效的session cookie")
                return False
            
            # 生成TOTP验证码
            totp = pyotp.TOTP(manual_code)
            otp_code = totp.now()
            logger.info(f"生成的OTP码: {otp_code}")
            
            # 设置请求headers和cookies
            headers = self.client.headers.copy()
            headers.update({
                'Referer': 'https://targon.com/two-factor-auth',
                'Origin': 'https://targon.com'
            })
            
            cookies = {'auth_session': self.session_cookie}
            
            # 构造启用2FA请求数据
            enable_2fa_data = {
                "0": {
                    "json": {
                        "otp": otp_code,
                        "twoFactorSecret": two_factor_secret
                    }
                }
            }
            
            # 发送启用2FA请求
            response = self.client.post(
                "https://targon.com/api/trpc/account.enable2FA?batch=1",
                json=enable_2fa_data,
                headers=headers,
                cookies=cookies
            )
            
            logger.info(f"启用2FA请求响应状态: {response.status_code}")
            
            if response.status_code == 200:
                logger.info("2FA启用成功")
                return True
            else:
                logger.error(f"启用2FA失败: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"启用2FA过程中发生错误: {e}")
            return False
    
    def get_api_keys(self, email):
        """
        获取API密钥
        
        Args:
            email: 用户邮箱
            
        Returns:
            list: API密钥列表，失败返回None
        """
        try:
            logger.info("开始获取API密钥")
            
            if not self.session_cookie:
                logger.error("没有有效的session cookie")
                return None
            
            # 设置请求headers和cookies
            headers = self.client.headers.copy()
            headers.update({
                'Referer': 'https://targon.com/settings'
            })
            
            cookies = {'auth_session': self.session_cookie}
            
            # 构造查询URL（包含多个API调用）
            query_url = f"https://targon.com/api/trpc/keys.getApiKeys,model.getPopularModels,account.getUserBookmarks,account.getUserInterest,account.getUserSubscription,account.check2FA,account.getTaoPrice,account.getAlphaPrice,notification.getNotifications?batch=1&input=%7B%220%22%3A%7B%22json%22%3Anull%2C%22meta%22%3A%7B%22values%22%3A%5B%22undefined%22%5D%7D%7D%2C%221%22%3A%7B%22json%22%3A%7B%22days%22%3A30%2C%22limit%22%3A3%7D%7D%2C%222%22%3A%7B%22json%22%3Anull%2C%22meta%22%3A%7B%22values%22%3A%5B%22undefined%22%5D%7D%7D%2C%223%22%3A%7B%22json%22%3Anull%2C%22meta%22%3A%7B%22values%22%3A%5B%22undefined%22%5D%7D%7D%2C%224%22%3A%7B%22json%22%3Anull%2C%22meta%22%3A%7B%22values%22%3A%5B%22undefined%22%5D%7D%7D%2C%225%22%3A%7B%22json%22%3A%7B%22email%22%3A%22{email}%22%7D%7D%2C%226%22%3A%7B%22json%22%3Anull%2C%22meta%22%3A%7B%22values%22%3A%5B%22undefined%22%5D%7D%7D%2C%227%22%3A%7B%22json%22%3Anull%2C%22meta%22%3A%7B%22values%22%3A%5B%22undefined%22%5D%7D%7D%2C%228%22%3A%7B%22json%22%3Anull%2C%22meta%22%3A%7B%22values%22%3A%5B%22undefined%22%5D%7D%7D%7D"
            
            # 发送获取API密钥请求
            response = self.client.get(
                query_url,
                headers=headers,
                cookies=cookies
            )
            
            logger.info(f"获取API密钥请求响应状态: {response.status_code}")
            
            if response.status_code == 200:
                response_data = response.json()
                
                if response_data and len(response_data) > 0:
                    # 第一个元素是API密钥信息
                    api_keys_data = response_data[0].get('result', {}).get('data', {}).get('json', [])
                    
                    if api_keys_data:
                        logger.info(f"成功获取到 {len(api_keys_data)} 个API密钥")
                        for key_info in api_keys_data:
                            logger.info(f"API密钥: {key_info.get('name')} - {key_info.get('key')}")
                        return api_keys_data
                    else:
                        logger.warning("未找到API密钥")
                        return []
                
                logger.error("API密钥响应数据格式不正确")
                return None
            else:
                logger.error(f"获取API密钥失败: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"获取API密钥过程中发生错误: {e}")
            return None
    
    def __del__(self):
        """确保HTTP客户端在对象销毁时关闭"""
        try:
            self.client.close()
        except:
            pass