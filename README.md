# Targon 账户注册机

这是一个用于自动注册 Targon 账户、激活邮箱、设置和启用 2FA 并获取 API 密钥的 Python 项目。

## 设置

1.  **克隆项目**

    ```bash
    git clone <your-repo-url>
    cd <your-repo-directory>
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
    export TARGON_EMAIL="your_email@example.com"
    export TARGON_PASSWORD="your_strong_password"
    export TARGON_ACTIVATION_LINK="your_activation_link"
    ```

    -   `TARGON_EMAIL`: 您要用于注册的邮箱地址。
    -   `TARGON_PASSWORD`: 您要用于账户的密码。
    -   `TARGON_ACTIVATION_LINK`: 从 Targon 收到的邮箱激活链接。

## 运行

设置好环境变量后，运行主程序：

```bash
python main.py
```

日志将保存在 `logs/app.log` 文件中。