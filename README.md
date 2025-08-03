# Targon 自动注册机 (Cloudflare 版)

这是一个用于自动批量注册 Targon 账户的 Python 脚本。此版本使用 **Cloudflare Email Routing** 配合您自己的域名来接收激活邮件，并通过 **IMAP** 自动读取邮件，实现更稳定、更可靠的注册流程。

## 功能

- 使用您自己的域名生成随机的临时邮箱地址
- 自动注册 Targon 账户
- 通过 IMAP 自动登录您的目标邮箱，获取激活链接
- 自动设置两步验证 (2FA)
- 自动获取并保存 API 密钥
- 支持单个或批量注册模式

## 环境要求

- 一个您拥有并已添加到 Cloudflare 的域名
- Python 3.6+
- Ubuntu / Debian 或其他 Linux 发行版

## 部署和使用方法

### 第 1 步：Cloudflare 设置

1.  **域名托管：** 确保您的域名已在 Cloudflare 成功托管。
2.  **启用邮件路由 (Email Routing)：**
    *   在 Cloudflare 仪表板中，导航到 `电子邮件` -> `电子邮件路由`。
    *   按照指引完成设置，这通常包括添加必要的 MX 和 TXT 记录。
3.  **设置目标地址：**
    *   在“目标地址”选项卡下，添加一个您能正常访问的真实邮箱（例如 `your-name@gmail.com`）并完成验证。所有临时邮箱收到的邮件都将转发到这里。
4.  **启用“全部捕获”地址 (Catch-all Address)：**
    *   在“路由规则”选项卡下，找到“全部捕获”地址 (Catch-all address) 的设置。
    *   **启用该功能**，并将“操作”设置为“发送到”，然后选择您上一步验证过的目标邮箱。
    *   启用后，任何发送到您域名下**不存在的自定义地址**（如 `random-string-123@your-domain.com`）的邮件，都将被自动转发到您的目标邮箱。

### 第 2 步：为您的目标邮箱生成应用密码

为了让脚本能安全地登录您的邮箱，您需要生成一个专用的“应用密码”。**不要直接使用您的主登录密码。**

-   **对于 Gmail:**
    1.  开启您 Google 账户的[两步验证](https://myaccount.google.com/security)。
    2.  访问 [Google 应用密码](https://myaccount.google.com/apppasswords) 页面。
    3.  在“选择应用”中选择“其他（自定义名称）”，输入一个名字（如 `TargonRegisterScript`），然后点击“生成”。
    4.  **立即复制并保存好生成的 16 位密码**。这个密码只会显示一次。

-   **对于其他邮箱服务商 (Outlook, etc.):** 请查阅其官方文档了解如何生成应用密码。

### 第 3 步：在 VPS 上配置项目

1.  **克隆或上传项目：**
    ```bash
    git clone https://github.com/justincnn/Targon-register
    cd [项目目录]
    ```

2.  **创建并填写配置文件：**
    *   首先，复制示例配置文件。
        ```bash
        cp config.json.example config.json
        ```
    *   然后，编辑 `config.json` 文件，填入您的信息。
        ```json
        {
          "domain": "your-domain.com",
          "imap_server": "imap.gmail.com",
          "imap_user": "your-real-email@gmail.com",
          "imap_password": "your-gmail-app-password"
        }
        ```
        -   `domain`: 您在 Cloudflare 设置的域名。
        -   `imap_server`: 您目标邮箱的 IMAP 服务器地址 (例如 Gmail 是 `imap.gmail.com`)。
        -   `imap_user`: 您的目标邮箱地址。
        -   `imap_password`: 您在上一步生成的 **16 位应用密码**。

### 第 4 步：安装依赖并运行

1.  **创建虚拟环境并安装依赖：**
    ```bash
    # (如果需要) sudo apt update && sudo apt install -y python3-venv
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    ```

2.  **运行程序：**
    ```bash
    python3 targon_register.py
    ```

## 注意事项

- 配置文件 `config.json` 已被添加到 `.gitignore` 中，不会被上传到您的 GitHub 仓库，以保护您的凭据安全。
- 脚本会搜索您目标邮箱收件箱中**发往临时邮箱**并且**未读**的邮件，以提高效率和准确性。