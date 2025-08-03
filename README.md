# Targon 账户注册机

这是一个用于自动注册 Targon 账户、激活邮箱、设置和启用 2FA 并获取 API 密钥的 Python 项目。

该项目利用 Cloudflare 的邮件路由功能自动创建临时邮箱进行注册，并使用 2Captcha 自动解决 Cloudflare Turnstile 质询。

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
    export TWOCAPTCHA_API_KEY="your_2captcha_api_key"
    export CF_API_TOKEN="your_cloudflare_api_token"
    export CF_ZONE_ID="your_cloudflare_zone_id"
    export CF_ACCOUNT_ID="your_cloudflare_account_id"
    export CF_DOMAIN="your_domain.com"
    ```

    -   `TARGON_PASSWORD`: 您要用于账户的密码。
    -   `TWOCAPTCHA_API_KEY`: 您的 2Captcha API 密钥。
    -   `CF_API_TOKEN`: 您的 Cloudflare API 令牌。
    -   `CF_ZONE_ID`: 您的 Cloudflare 区域 ID。
    -   `CF_ACCOUNT_ID`: 您的 Cloudflare 帐户 ID。
    -   `CF_DOMAIN`: 您要用于邮件路由的域名。

### 如何获取 Cloudflare 凭据

1.  **`CF_ACCOUNT_ID` (账户 ID)**:
    *   登录到您的 Cloudflare 仪表板。
    *   在主页右侧，您会看到您的账户 ID。点击“点击复制”即可。

2.  **`CF_ZONE_ID` (区域 ID)**:
    *   在 Cloudflare 仪表板上，选择您要使用的域名。
    *   在域名的“概述”页面，向下滚动，您会在右侧找到“区域 ID”。点击“点击复制”即可。

3.  **`CF_API_TOKEN` (API 令牌)**:
    *   在 Cloudflare 仪表板上，点击右上角您的个人资料图标，然后选择“我的个人资料”。
    *   在左侧菜单中，选择“API 令牌”。
    *   点击“创建令牌”。
    *   选择一个模板（例如，“编辑区域 DNS”），或者创建一个具有所需权限的自定义令牌。对于邮件路由，您可能需要“区域.区域”和“区域.DNS”的编辑权限。
    *   在“区域资源”部分，选择您要应用此令牌的特定区域。
    *   点击“继续以显示摘要”，然后点击“创建令牌”。
    *   **重要提示：** Cloudflare 只会显示一次 API 令牌。请务必在关闭页面前复制并安全地保存它。

## 重要提示

-   **创建邮件路由规则**: `cloudflare_email.py` 中的 `create_temp_email` 函数目前是一个占位符。您需要使用 Cloudflare API 在您的域上创建一个邮件路由规则，将发送到临时地址的邮件转发到您的真实邮箱。

-   **获取激活链接**: `cloudflare_email.py` 中的 `get_activation_link` 函数也是一个占位符。您需要实现一种方法来访问您的真实邮箱收件箱，并从 Targon 发送的激活邮件中解析出激活链接。

## 运行

设置好环境变量并实现上述占位符函数后，运行主程序：

```bash
python main.py
```

日志将保存在 `logs/app.log` 文件中。

## 故障排除

-   **`ERROR_ZERO_BALANCE`**: 如果您在运行脚本时看到此错误，则表示您的 2Captcha 账户余额不足。请访问 2Captcha 网站为您的账户充值。
