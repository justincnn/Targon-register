import os
from loguru import logger
from targon_register import TargonRegistrar

def main():
    logger.add("logs/app.log", rotation="10 MB", retention="7 days", level="INFO")

    email = os.getenv("TARGON_EMAIL")
    password = os.getenv("TARGON_PASSWORD")
    activation_link = os.getenv("TARGON_ACTIVATION_LINK")

    if not all([email, password, activation_link]):
        logger.error("请设置 TARGON_EMAIL, TARGON_PASSWORD, 和 TARGON_ACTIVATION_LINK 环境变量。")
        return

    registrar = TargonRegistrar()

    # 1. 注册账户
    if registrar.register_account(email, password):
        # 2. 激活邮箱
        if registrar.activate_email(activation_link):
            # 3. 创建 2FA
            two_fa_data = registrar.create_2fa()
            if two_fa_data:
                # 4. 启用 2FA
                if registrar.enable_2fa(two_fa_data['two_factor_secret'], two_fa_data['manual_code']):
                    # 5. 获取 API 密钥
                    registrar.get_api_keys(email)

if __name__ == "__main__":
    main()