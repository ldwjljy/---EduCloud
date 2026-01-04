# 临时报告文件说明

本目录存放临时生成的报告文件。

## 📄 文件列表

### migration_file_report.json
- **生成时间**：2025-12-02
- **生成工具**：`accounts/management/commands/verify_files.py`
- **用途**：数据库迁移文件完整性校验报告
- **说明**：用于验证文件迁移的完整性，包含文件数量、内容校验、权限检查等信息
- **是否可以删除**：✅ 是，可以删除，需要时可重新生成
- **重新生成方法**：
  ```bash
  python manage.py verify_files --src <源目录> --dst <目标目录> --output migration_file_report.json
  ```

## ⚠️ 注意事项

- 这些文件是临时生成的，可以随时删除
- 删除后不影响项目功能
- 如需验证文件完整性，可以重新运行命令生成报告
