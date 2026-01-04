# EduCloud 教务云管理系统

一个基于Django的现代化教育管理系统，为高校和教育机构提供全方位的教务管理解决方案。系统采用模块化设计，支持多角色权限管理，提供直观的用户界面和强大的功能支持。

## ✨ 核心特性

### 🎯 主要功能模块

- **📚 课程管理**
  - 课程信息管理（创建、编辑、删除）
  - 智能排课系统（自动检测时间冲突）
  - 拖拽式课表编辑（直观可视化操作）
  - 双击快速编辑课程信息
  - 跨学院授课支持
  - 课程搜索与筛选

- **👥 学生管理**
  - 学生信息管理（基本信息、学籍信息）
  - 学生档案维护
  - 班级管理
  - 批量导入导出

- **👨‍🏫 教师管理**
  - 教师信息管理
  - 职务管理（院长、副院长、班主任、教师）
  - 权限分配
  - 角色验证（不同角色字段验证规则）

- **📊 成绩管理**
  - 成绩录入与编辑
  - 成绩统计分析
  - 成绩查询与导出
  - 成绩报表生成

- **✅ 考勤管理**
  - 考勤记录管理
  - 考勤统计与分析
  - 考勤报表

- **🏢 组织架构管理**
  - 学院管理（支持启用/停用状态）
  - 专业管理（支持多种学制类型）
  - 班级管理（自动命名规则）
  - 树形结构展示

- **🏫 教室管理**
  - 教室信息管理
  - 教室分配与调度
  - 使用情况统计

- **📅 日历应用**
  - 课程日历展示
  - 事件管理
  - 待办事项提醒

- **📢 通知管理**
  - 系统通知发布
  - 通知分类管理
  - 通知可见性控制

- **📝 考试管理**
  - 考试安排
  - 考试信息管理

### 🚀 技术特性

- **现代化技术栈**：基于Django 4.2 + Django REST Framework
- **数据库支持**：MySQL 5.7+ / MySQL 8.0+
- **权限管理**：基于RBAC的细粒度权限控制
- **用户角色**：支持系统管理员、学院管理员、教师、学生等多种角色
- **数据导入导出**：支持Excel批量导入导出
- **智能工具**：一键检查、自动初始化、智能启动脚本
- **响应式设计**：适配PC和移动设备

### 💡 特色功能

- ✅ **智能排课**：自动检测时间冲突，避免课程安排冲突
- ✅ **拖拽排课**：直观的拖拽操作，快速调整课程时间
- ✅ **双击编辑**：双击课表课程即可快速编辑
- ✅ **统一弹窗**：美观的自定义弹窗系统，提升用户体验
- ✅ **冲突检测**：实时检测教室、教师、班级时间冲突
- ✅ **数据校验**：完善的数据验证机制，确保数据准确性

## 环境要求

- Python 3.8+
- MySQL 5.7+ 或 MySQL 8.0+
- pip（Python包管理器）

## 快速开始

### 方式一：一键启动（最简单）

克隆项目后，直接运行启动脚本：

```bash
# 1. 克隆项目
git clone <repository-url>
cd EduCloud

# 2. Windows用户：双击 start.bat 或运行
start.bat

# Linux/Mac用户：运行
python start.py
```

启动脚本会自动：
- ✅ 检查Python版本
- ✅ 检查并自动安装缺失的依赖包
- ✅ 创建.env配置文件（如果不存在）
- ✅ 启动Django服务器

**首次运行还需要：**
1. 编辑 `.env` 文件配置数据库
2. 创建数据库：`CREATE DATABASE educloud CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;`
3. 运行数据库迁移：`python manage.py migrate`
4. 创建超级管理员：`python manage.py createsuperuser`

### 方式二：使用初始化脚本（完整设置）

```bash
# 1. 克隆项目
git clone <repository-url>
cd EduCloud

# 2. 创建虚拟环境（推荐）
# Windows:
python -m venv venv
venv\Scripts\activate

# Linux/Mac:
python3 -m venv venv
source venv/bin/activate

# 3. 运行初始化脚本
python setup.py
```

初始化脚本会自动完成：
- 创建.env配置文件
- 安装所有依赖
- 运行数据库迁移
- 可选创建超级管理员账户
- 收集静态文件

### 方式二：手动设置

### 1. 克隆项目

```bash
git clone <repository-url>
cd EduCloud
```

### 2. 创建虚拟环境（推荐）

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

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 配置环境变量

复制环境变量模板文件：
```bash
# Windows
copy .env.example .env

# Linux/Mac
cp .env.example .env
```

编辑 `.env` 文件，根据你的实际情况修改以下配置：

```env
# Django配置
SECRET_KEY=your-secret-key-here-change-this-in-production
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# 数据库配置
DB_NAME=educloud
DB_USER=root
DB_PASSWORD=你的数据库密码
DB_HOST=127.0.0.1
DB_PORT=3306

# 学期配置（可选）
SEMESTER_START_DATE=2024-09-02
SEMESTER_TOTAL_WEEKS=18
```

### 5. 创建数据库

在MySQL中创建数据库：

**方法一：使用MySQL命令行**
```sql
CREATE DATABASE educloud CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

**方法二：使用MySQL Workbench或其他GUI工具**
1. 打开MySQL客户端
2. 创建新数据库，名称：`educloud`
3. 字符集选择：`utf8mb4`
4. 排序规则选择：`utf8mb4_unicode_ci`

**注意：** 如果数据库不存在，Django迁移可能会失败。请确保先创建数据库。

### 6. 运行数据库迁移

```bash
python manage.py migrate
```

### 7. 创建超级管理员（可选）

```bash
python manage.py createsuperuser
```

### 8. 启动开发服务器

**方式一：使用智能启动脚本（推荐）**

智能启动脚本会自动检查并安装缺失的依赖包：

```bash
# Windows
start.bat
# 或双击 start.bat 文件

# Linux/Mac
chmod +x start.sh  # 首次运行需要添加执行权限
./start.sh
# 或直接运行
python start.py
```

**方式二：直接启动**

```bash
python manage.py runserver
```

服务器将在 `http://127.0.0.1:8000` 启动。

**智能启动脚本功能：**
- ✅ 自动检查Python版本
- ✅ 自动检查并安装缺失的依赖包
- ✅ 自动创建.env配置文件（如果不存在）
- ✅ 一键启动Django服务器

## 项目结构

```
EduCloud/
├── EduCloud/          # Django项目主配置目录
│   ├── settings.py    # 项目设置
│   ├── urls.py        # URL路由配置
│   └── ...
├── accounts/          # 账户管理应用
├── organization/      # 组织架构管理
├── courses/           # 课程管理
├── attendance_app/    # 考勤管理
├── grades/            # 成绩管理
├── notices/           # 通知管理
├── calendarapp/       # 日历应用
├── classrooms/        # 教室管理
├── static/            # 静态文件（CSS、JS、图片）
├── templates/         # HTML模板
├── manage.py          # Django管理脚本
├── requirements.txt   # Python依赖列表
└── README.md          # 项目说明文档
```

## 配置检查

### 使用一键检查工具（推荐）

所有检查工具已整合到 `一键检查` 目录中：

```bash
# Windows: 双击运行
一键检查\一键检查.bat

# Linux/Mac: 运行
chmod +x 一键检查/一键检查.sh
./一键检查/一键检查.sh

# 或直接运行Python脚本
python 一键检查/一键检查.py
```

一键检查工具提供以下功能：
1. **项目配置检查** - 检查文件、环境变量、依赖、数据库连接
2. **项目初始化** - 自动完成项目初始设置
3. **导入前检查** - 检查数据导入的前置条件
4. **周五时间段检查** - 检查时间段配置
5. **执行所有检查** - 一键运行所有检查

### 单独运行检查脚本

```bash
# 项目配置检查
python 一键检查/check_setup.py

# 项目初始化
python 一键检查/setup.py

# 导入前检查
python 一键检查/check_before_import.py

# 周五时间段检查
python 一键检查/check_friday_slots.py
```

## 常见问题

### 1. 数据库连接失败

- 确保MySQL服务已启动
- 检查 `.env` 文件中的数据库配置是否正确
- 确认数据库用户有足够的权限
- 确认数据库已创建（名称与 `.env` 中的 `DB_NAME` 一致）

### 2. 模块导入错误

- 确保已安装所有依赖：`pip install -r requirements.txt`
- 确保虚拟环境已激活

### 3. 静态文件无法加载

运行以下命令收集静态文件：
```bash
python manage.py collectstatic
```

### 4. 迁移文件冲突

如果遇到迁移文件冲突，可以重置迁移：
```bash
# 注意：这会删除所有迁移文件，请谨慎使用
python manage.py migrate --fake-initial
```

## 🔧 工具使用

项目中的工具脚本已整理到 `工具/` 目录，按功能分类：

### 数据库工具
- **数据库导出**：`工具/01-数据库工具/export_database_to_mysql.py`
  - Windows快速运行：双击 `工具/01-数据库工具/export_database.bat`
  - 详细说明：查看 `工具/01-数据库工具/README.md`

### 时间段工具
- **生成时间段**：`工具/02-时间段工具/generate_timeslots.py`
  - Windows快速运行：双击 `工具/02-时间段工具/generate_timeslots.bat`
  - 详细说明：查看 `工具/02-时间段工具/README.md`

更多工具说明请查看：[工具/README.md](./工具/README.md)

### 项目检查工具
- **一键检查**：`一键检查/一键检查.py`
  - Windows快速运行：双击 `一键检查/一键检查.bat`
  - 详细说明：查看 `一键检查/README.md`

### 部署检查工具
- **部署检查**：`check_deployment.py`
  - 运行方式：`python check_deployment.py`

## 开发说明

### 添加新的应用

1. 创建应用：
```bash
python manage.py startapp app_name
```

2. 在 `EduCloud/settings.py` 的 `INSTALLED_APPS` 中添加应用名称

3. 创建并运行迁移：
```bash
python manage.py makemigrations
python manage.py migrate
```

### 代码规范

- 遵循PEP 8 Python代码规范
- 使用有意义的变量和函数名
- 添加必要的注释和文档字符串

## 📚 项目文档

项目文档已分类整理，详细内容请查看：

- **📖 [说明文档索引](./说明文档/README.md)** - 完整的文档导航和分类
- **🚀 [部署指南](./DEPLOYMENT.md)** - 详细的部署说明
- **✅ [部署检查清单](./部署检查清单.md)** - 部署前检查清单

### 文档分类

- **[01-使用指南](./说明文档/01-使用指南/)** - 用户使用指南
- **[02-技术文档](./说明文档/02-技术文档/)** - 技术实现文档
- **[03-修复记录](./说明文档/03-修复记录/)** - 问题修复记录
- **[05-课程管理](./说明文档/05-课程管理/)** - 课程管理功能说明

### 快速查找

- **如何快速开始？** → [快速开始指南](./说明文档/01-使用指南/QUICK_START.md)
- **如何部署项目？** → [部署指南](./DEPLOYMENT.md)
- **如何使用课程管理？** → [课程管理使用指南](./说明文档/01-使用指南/课程管理使用指南.md)

## 📄 许可证

本项目仅供个人学习和展示使用。

---
由 [(♡>𖥦<) /♥](https://github.com/ldwjljy) 倾情打造
