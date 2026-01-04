# EduCloud 部署指南

本文档提供完整的项目部署说明，适用于在不同环境中一键部署。

## 目录

- [系统要求](#系统要求)
- [快速部署](#快速部署)
- [详细部署步骤](#详细部署步骤)
- [生产环境部署](#生产环境部署)
- [常见问题](#常见问题)
- [部署检查清单](#部署检查清单)

## 系统要求

### 基础环境

- **Python**: 3.8 或更高版本
- **MySQL**: 5.7+ 或 MySQL 8.0+
- **操作系统**: Windows / Linux / macOS

### Python 依赖

所有依赖已在 `requirements.txt` 中列出：
- Django==5.2.7
- djangorestframework==3.15.2
- django-filter==24.2
- PyMySQL==1.1.1
- python-dotenv==1.0.0

## 快速部署

### 方式一：使用一键部署脚本（推荐）

#### Windows

```bash
# 双击运行或在命令行执行
deploy.bat
```

#### Linux/Mac

```bash
# 添加执行权限
chmod +x deploy.sh

# 运行部署脚本
./deploy.sh
```

一键部署脚本会自动完成：
1. ✅ 检查Python环境
2. ✅ 创建.env配置文件
3. ✅ 安装所有依赖
4. ✅ 运行数据库迁移
5. ✅ 收集静态文件
6. ✅ 可选创建超级管理员

### 方式二：手动部署

参见[详细部署步骤](#详细部署步骤)

## 详细部署步骤

### 1. 获取项目代码

```bash
# 从Git仓库克隆
git clone <repository-url>
cd EduCloud

# 或解压项目压缩包
unzip EduCloud.zip
cd EduCloud
```

### 2. 创建Python虚拟环境（推荐）

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**Linux/Mac:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. 配置环境变量

复制环境变量模板文件：

**Windows:**
```bash
copy .env.example .env
```

**Linux/Mac:**
```bash
cp .env.example .env
```

编辑 `.env` 文件，配置以下内容：

```env
# Django配置
SECRET_KEY=你的随机密钥字符串
DEBUG=False  # 生产环境设为False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# 数据库配置
DB_NAME=educloud
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_HOST=127.0.0.1
DB_PORT=3306

# 学期配置（可选）
SEMESTER_START_DATE=2024-09-01
SEMESTER_TOTAL_WEEKS=20
```

**重要提示：**
- `SECRET_KEY` 必须是随机生成的字符串
- 生产环境必须设置 `DEBUG=False`
- `ALLOWED_HOSTS` 必须包含你的域名

### 4. 安装依赖

```bash
pip install -r requirements.txt
```

### 5. 创建数据库

在MySQL中创建数据库：

```sql
CREATE DATABASE educloud CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

确保数据库用户有足够权限：
```sql
GRANT ALL PRIVILEGES ON educloud.* TO 'your_db_user'@'localhost';
FLUSH PRIVILEGES;
```

### 6. 运行数据库迁移

```bash
python manage.py migrate
```

### 7. 收集静态文件

```bash
python manage.py collectstatic --noinput
```

### 8. 创建超级管理员（可选）

```bash
python manage.py createsuperuser
```

按提示输入用户名、邮箱和密码。

### 9. 测试运行

```bash
python manage.py runserver
```

访问 http://127.0.0.1:8000 检查是否正常运行。

## 生产环境部署

### 使用 Gunicorn + Nginx

#### 1. 安装 Gunicorn

```bash
pip install gunicorn
```

将 `gunicorn` 添加到 `requirements.txt` 中。

#### 2. 创建 Gunicorn 配置文件

创建 `gunicorn_config.py`:

```python
bind = "127.0.0.1:8000"
workers = 4
worker_class = "sync"
timeout = 120
keepalive = 5
max_requests = 1000
max_requests_jitter = 100
```

#### 3. 启动 Gunicorn

```bash
gunicorn EduCloud.wsgi:application --config gunicorn_config.py
```

#### 4. 配置 Nginx

创建 `/etc/nginx/sites-available/educloud`:

```nginx
server {
    listen 80;
    server_name yourdomain.com;

    # 静态文件
    location /static/ {
        alias /path/to/EduCloud/staticfiles/;
    }

    # 媒体文件
    location /media/ {
        alias /path/to/EduCloud/media/;
    }

    # Django应用
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

启用配置：
```bash
ln -s /etc/nginx/sites-available/educloud /etc/nginx/sites-enabled/
nginx -t  # 测试配置
systemctl reload nginx
```

#### 5. 配置 Systemd 服务（Linux）

创建 `/etc/systemd/system/educloud.service`:

```ini
[Unit]
Description=EduCloud Gunicorn daemon
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/path/to/EduCloud
ExecStart=/path/to/venv/bin/gunicorn EduCloud.wsgi:application --config gunicorn_config.py

[Install]
WantedBy=multi-user.target
```

启动服务：
```bash
systemctl daemon-reload
systemctl enable educloud
systemctl start educloud
```

### 使用 Supervisor 管理进程

安装 Supervisor:
```bash
pip install supervisor
```

配置文件示例：
```ini
[program:educloud]
command=/path/to/venv/bin/gunicorn EduCloud.wsgi:application --config gunicorn_config.py
directory=/path/to/EduCloud
user=www-data
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/educloud.log
```

## 常见问题

### 1. 数据库连接失败

**问题**: `django.db.utils.OperationalError: (2003, "Can't connect to MySQL server")`

**解决方案**:
- 检查MySQL服务是否启动
- 检查 `.env` 文件中的数据库配置
- 检查数据库用户权限
- 检查防火墙设置

### 2. 静态文件无法加载

**问题**: CSS/JS文件404错误

**解决方案**:
```bash
# 重新收集静态文件
python manage.py collectstatic --noinput

# 检查STATIC_ROOT配置
# 检查Nginx/Apache静态文件配置
```

### 3. 权限错误

**问题**: `Permission denied`

**解决方案**:
```bash
# Linux/Mac: 检查文件权限
chmod -R 755 /path/to/EduCloud
chown -R www-data:www-data /path/to/EduCloud
```

### 4. SECRET_KEY警告

**问题**: Django警告使用默认SECRET_KEY

**解决方案**:
- 在 `.env` 文件中设置随机SECRET_KEY
- 生成方式: `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`

## 部署检查清单

在部署前，请确认以下各项：

### 环境准备
- [ ] Python 3.8+ 已安装
- [ ] MySQL已安装并启动
- [ ] 虚拟环境已创建（推荐）

### 配置文件
- [ ] `.env` 文件已创建并配置
- [ ] `SECRET_KEY` 已设置为随机值
- [ ] `DEBUG=False`（生产环境）
- [ ] `ALLOWED_HOSTS` 已正确配置
- [ ] 数据库配置正确

### 数据库
- [ ] 数据库已创建
- [ ] 数据库字符集为 utf8mb4
- [ ] 数据库用户有足够权限
- [ ] 数据库迁移已运行

### 依赖和静态文件
- [ ] 所有依赖已安装 (`pip install -r requirements.txt`)
- [ ] 静态文件已收集 (`python manage.py collectstatic`)

### 安全配置
- [ ] `DEBUG=False`（生产环境）
- [ ] `SECRET_KEY` 已更改
- [ ] SSL证书已配置（如果使用HTTPS）
- [ ] 防火墙规则已配置

### 服务配置
- [ ] Gunicorn/WSGI服务器已配置
- [ ] Nginx/Apache已配置
- [ ] 进程管理器（Supervisor/Systemd）已配置
- [ ] 日志文件路径已配置

### 测试
- [ ] 应用可以正常启动
- [ ] 静态文件可以正常访问
- [ ] 数据库连接正常
- [ ] 用户登录功能正常
- [ ] 主要功能模块正常

## 部署后维护

### 更新代码

```bash
# 1. 备份数据库
mysqldump -u user -p educloud > backup.sql

# 2. 拉取最新代码
git pull  # 或手动更新文件

# 3. 安装新依赖
pip install -r requirements.txt

# 4. 运行数据库迁移
python manage.py migrate

# 5. 收集静态文件
python manage.py collectstatic --noinput

# 6. 重启服务
systemctl restart educloud  # 或 supervisorctl restart educloud
```

### 日志查看

```bash
# Gunicorn日志
tail -f /var/log/educloud.log

# Nginx日志
tail -f /var/log/nginx/error.log
tail -f /var/log/nginx/access.log

# Django日志（如果配置了）
tail -f /path/to/EduCloud/logs/django.log
```

## 技术支持

如遇到问题，请：
1. 查看本文档的[常见问题](#常见问题)部分
2. 检查项目的README.md文件
3. 运行配置检查脚本: `python 一键检查/check_setup.py`
4. 查看项目日志文件

---

**最后更新**: 2024年

