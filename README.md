# Targon 账户注册机

这是一个用于自动注册 Targon 账户、激活邮箱、设置和启用 2FA 并获取 API 密钥的 Python 项目。

该项目利用 Cloudflare 的邮件路由功能自动创建临时邮箱进行注册。

## 设置

1.  **克隆项目**

    ```bash
    git clone https://github.com/justincnn/Targon-register
    cd Targon-register
    ```

2.  **创建并激活虚拟环境**

    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **安装依赖**

    ```bash
    pip install -r requirements.txt
    ```

4.  **设置环境变量**

    在运行项目之前，您需要设置以下环境变量：

    ```bash
    export TARGON_PASSWORD="your_strong_password"
    export CF_API_TOKEN="your_cloudflare_api_token"
    export CF_ZONE_ID="your_cloudflare_zone_id"
    export CF_ACCOUNT_ID="your_cloudflare_account_id"
    export CF_DOMAIN="your_domain.com"
    ```

    -   `TARGON_PASSWORD`: 您要用于账户的密码。
    -   `CF_API_TOKEN`: 您的 Cloudflare API 令牌。
    -   `CF_ZONE_ID`: 您的 Cloudflare 区域 ID。
    -   `CF_ACCOUNT_ID`: 您的 Cloudflare 帐户 ID。
    -   `CF_DOMAIN`: 您要用于邮件路由的域名。

## 重要提示

-   **创建邮件路由规则**: `cloudflare_email.py` 中的 `create_temp_email` 函数目前是一个占位符。您需要使用 Cloudflare API 在您的域上创建一个邮件路由规则，将发送到临时地址的邮件转发到您的真实邮箱。

-   **获取激活链接**: `cloudflare_email.py` 中的 `get_activation_link` 函数也是一个占位符。您需要实现一种方法来访问您的真实邮箱收件箱，并从 Targon 发送的激活邮件中解析出激活链接。

## 运行

设置好环境变量并实现上述占位符函数后，运行主程序：

```bash
python main.py
```

日志将保存在 `logs/app.log` 文件中。