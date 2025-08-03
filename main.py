import os
import uuid
import time
from loguru import logger
from DrissionPage import ChromiumPage
from targon_register import TargonRegistrar
from cloudflare_email import CloudflareEmail

def solve_turnstile_with_browser():
    """
    使用 DrissionPage 尝试解决 Cloudflare Turnstile
    """
    try:
        page = ChromiumPage()
        page.get('https://targon.com/auth/sign-up')
        
        # 等待 Turnstile 加载并获取令牌
        # 这可能需要一些时间，具体取决于网络和 Cloudflare 的响应
        time.sleep(10) # 等待 10 秒

        # 尝试从页面中提取令牌
        # 注意：这假设令牌存在于一个具有特定名称或ID的隐藏输入字段中
        # 这可能需要根据 Targon 网站的实际情况进行调整
        token_element = page.ele('input[name="cf-turnstile-response"]')
        if token_element:
            token = token_element.value
            logger.info("成功获取 Turnstile 令牌。")
            page.quit()
            return token
        else:
            logger.error("无法找到 Turnstile 令牌元素。")
            page.quit()
            return None

    except Exception as e:
        logger.error(f"使用浏览器解决 Turnstile 时出错: {e}")
        return None

def main():
    logger.add("logs/app.log", rotation="10 MB", retention="7 days", level="INFO")

    # Targon 凭据
    password = os.getenv("TARGON_PASSWORD", "your_strong_password")

    # Cloudflare 凭据
    cf_api_token = os.getenv("CF_API_TOKEN")
    cf_zone_id = os.getenv("CF_ZONE_ID")
    cf_account_id = os.getenv("CF_ACCOUNT_ID")
    cf_domain = os.getenv("CF_DOMAIN")

    if not all([cf_api_token, cf_zone_id, cf_account_id, cf_domain]):
        logger.error("请设置 CF_API_TOKEN, CF_ZONE_ID, CF_ACCOUNT_ID, 和 CF_DOMAIN 环境变量。")
        return

    # 1. 解决 Turnstile
    turnstile_token = solve_turnstile_with_browser()
    if not turnstile_token:
        return

    # 2. 创建 CloudflareEmail 实例
    cf_email = CloudflareEmail(
        api_token=cf_api_token,
        zone_id=cf_zone_id,
        account_id=cf_account_id,
        domain=cf_domain
    )

    # 3. 创建临时邮箱
    email_prefix = str(uuid.uuid4())[:8]
    temp_email = cf_email.create_temp_email(email_prefix)

    # 4. 注册 Targon 账户
    registrar = TargonRegistrar()
    if registrar.register_account(temp_email, password, turnstile_token):
        # 5. 获取激活链接 (需要您自己实现)
        activation_link = cf_email.get_activation_link(temp_email)

        if activation_link:
            # 6. 激活邮箱
            if registrar.activate_email(activation_link):
                # 7. 创建 2FA
                two_fa_data = registrar.create_2fa()
                if two_fa_data:
                    # 8. 启用 2FA
                    if registrar.enable_2fa(two_fa_data['two_factor_secret'], two_fa_data['manual_code']):
                        # 9. 获取 API 密钥
                        registrar.get_api_keys(temp_email)

if __name__ == "__main__":
    main()