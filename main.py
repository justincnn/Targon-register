import os
import uuid
from loguru import logger
from targon_register import TargonRegistrar
from cloudflare_email import CloudflareEmail

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

    # 1. 创建 CloudflareEmail 实例
    cf_email = CloudflareEmail(
        api_token=cf_api_token,
        zone_id=cf_zone_id,
        account_id=cf_account_id,
        domain=cf_domain
    )

    # 2. 创建临时邮箱
    email_prefix = str(uuid.uuid4())[:8]
    temp_email = cf_email.create_temp_email(email_prefix)

    # 3. 注册 Targon 账户
    registrar = TargonRegistrar()
    if registrar.register_account(temp_email, password):
        # 4. 获取激活链接 (需要您自己实现)
        activation_link = cf_email.get_activation_link(temp_email)

        if activation_link:
            # 5. 激活邮箱
            if registrar.activate_email(activation_link):
                # 6. 创建 2FA
                two_fa_data = registrar.create_2fa()
                if two_fa_data:
                    # 7. 启用 2FA
                    if registrar.enable_2fa(two_fa_data['two_factor_secret'], two_fa_data['manual_code']):
                        # 8. 获取 API 密钥
                        registrar.get_api_keys(temp_email)

if __name__ == "__main__":
    main()