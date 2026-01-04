# 工具目录

本目录存放项目中的各种工具脚本，按功能分类整理。

## 📁 目录结构

```
工具/
├── 01-数据库工具/        # 数据库相关工具
├── 02-时间段工具/        # 时间段生成工具
└── README.md            # 本说明文件
```

## 📋 工具分类说明

### 01-数据库工具/
存放数据库相关的工具脚本。

**工具列表：**
- `export_database_to_mysql.py` - 数据库导出工具
  - 功能：将Django数据库导出为MySQL INSERT语句
  - 使用方法：`python 工具/01-数据库工具/export_database_to_mysql.py`
  - 批处理：`export_database.bat`（Windows快速运行）
  - 说明文档：`数据库导出说明.md`

### 02-时间段工具/
存放时间段生成相关的工具脚本。

**工具列表：**
- `generate_timeslots.py` - 生成标准时间段工具
  - 功能：生成标准的上课时间段数据
  - 使用方法：`python 工具/02-时间段工具/generate_timeslots.py`
  - 批处理：`generate_timeslots.bat`（Windows快速运行）

## 🚀 快速使用

### 数据库导出
```bash
# Windows: 双击运行
工具\01-数据库工具\export_database.bat

# 命令行运行
python 工具/01-数据库工具/export_database_to_mysql.py
```

### 生成时间段
```bash
# Windows: 双击运行
工具\02-时间段工具\generate_timeslots.bat

# 命令行运行
python 工具/02-时间段工具/generate_timeslots.py
```

## 📝 工具说明

每个工具目录都包含：
- Python脚本文件（.py）
- Windows批处理文件（.bat，如果有）
- README.md说明文档（详细使用说明）

## ⚠️ 注意事项

1. **运行环境**：所有工具都需要Django环境，确保已配置好数据库
2. **权限要求**：某些工具需要数据库读写权限
3. **备份数据**：运行可能修改数据的工具前，建议先备份数据库
4. **查看说明**：使用前请查看对应工具的README.md了解详细用法

---

*最后更新：2024年*
