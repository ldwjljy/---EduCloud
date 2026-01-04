# 数据库工具说明

本目录存放数据库相关的工具脚本。

## 📄 工具列表

### export_database_to_mysql.py
- **功能**：将Django项目的MySQL数据库中的所有数据导出为标准的MySQL INSERT语句SQL文件
- **用途**：数据库备份、数据迁移、数据导出
- **使用方法**：
  ```bash
  # 直接运行
  python 工具/01-数据库工具/export_database_to_mysql.py
  
  # 指定输出文件名
  python 工具/01-数据库工具/export_database_to_mysql.py my_export.sql
  ```
- **Windows快速运行**：双击 `export_database.bat`

### export_database.bat
- **功能**：Windows批处理文件，快速运行数据库导出工具
- **使用方法**：双击运行即可

## 📋 导出内容

脚本会自动导出以下内容：

1. **所有Django应用的数据表**
   - django.contrib.auth（用户认证）
   - django.contrib.contenttypes（内容类型）
   - django.contrib.sessions（会话）
   - django.contrib.admin（管理后台）
   - accounts（账户）
   - organization（组织架构）
   - personnel（人员管理）
   - courses（课程）
   - attendance_app（考勤）
   - grades（成绩）
   - notices（通知）
   - calendarapp（日历）
   - classrooms（教室）
   - students（学生）
   - exams（考试）
   - teachers（教师）
   - system（系统）

2. **多对多关系表**
   - 自动检测并导出所有多对多关系中间表

## 📝 导出文件格式

生成的SQL文件包含：
- 文件头信息（生成时间、数据库名等）
- 事务控制语句（SET FOREIGN_KEY_CHECKS=0等）
- 按应用分组的INSERT语句
- 文件尾（COMMIT语句）

## 🔄 导入数据

要导入导出的SQL文件到MySQL数据库：

```bash
mysql -u root -p educloud < database_export.sql
```

或者在MySQL客户端中：
```sql
source database_export.sql;
```

## ⚠️ 注意事项

1. **数据库连接**：确保数据库配置正确（在 `EduCloud/settings.py` 中）
2. **权限**：确保有读取数据库的权限
3. **文件大小**：如果数据量很大，生成的SQL文件可能会很大
4. **字符编码**：文件使用UTF-8编码，确保MySQL数据库也使用UTF-8编码
5. **外键约束**：导出时会临时禁用外键检查，导入时会自动恢复

## 💡 技术特点

- ✅ 自动检测所有Django模型
- ✅ 批量处理，避免内存溢出
- ✅ 正确处理外键关系
- ✅ 支持多对多关系表
- ✅ 完善的错误处理
- ✅ 详细的导出日志

## ❓ 常见问题

**Q: 导出失败怎么办？**
A: 检查数据库连接配置，确保数据库服务正在运行，并且有足够的权限。

**Q: 可以只导出特定应用的数据吗？**
A: 可以修改脚本中的 `installed_apps` 列表，只包含需要导出的应用。

**Q: 导出的SQL文件很大怎么办？**
A: 可以使用压缩工具压缩SQL文件，或者分批导出不同应用的数据。

## 📚 详细说明

更多详细信息请查看：`数据库导出说明.md`（项目根目录）
