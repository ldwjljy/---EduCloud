# Vendor 库文件说明

本目录包含项目所需的所有第三方库本地副本，已替换原先的CDN引用。

## 包含的库

### Bootstrap 5.3.0
- **路径**: `bootstrap/css/bootstrap.min.css`, `bootstrap/js/bootstrap.bundle.min.js`
- **原CDN**: https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/
- **用途**: 前端UI框架，提供响应式布局和组件

### FontAwesome 6.4.0
- **路径**: `fontawesome/css/all.min.css`, `fontawesome/webfonts/`
- **原CDN**: https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/
- **用途**: 图标字体库
- **注意**: CSS文件使用相对路径引用webfonts文件夹中的字体文件

### ECharts 5.4.3
- **路径**: `echarts/echarts.min.js`
- **原CDN**: https://cdn.jsdelivr.net/npm/echarts@5.4.3/
- **用途**: 数据可视化图表库

### Three.js 0.155.0
- **路径**: `three/three.min.js`
- **原CDN**: https://cdn.jsdelivr.net/npm/three@0.155.0/
- **用途**: 3D图形库，用于dashboard-3d页面

### SheetJS (xlsx) 0.20.1
- **路径**: `sheetjs/xlsx.full.min.js`
- **原CDN**: https://cdn.sheetjs.com/xlsx-0.20.1/
- **用途**: Excel文件读写库，用于导入导出功能

## 已更新的模板文件

以下模板文件已更新为引用本地资源：
- `templates/base.html`
- `templates/dashboard-3d.html`
- `templates/accounts/login.html`
- `templates/accounts/forgot_password.html`
- `templates/accounts/register.html`
- `templates/teachers.html`
- `templates/students.html`
- `templates/org.html`

## 好处

1. **离线访问**: 项目可以在没有互联网连接的环境中运行
2. **加载速度**: 减少外部网络请求，提高页面加载速度
3. **稳定性**: 避免CDN服务中断导致的功能异常
4. **版本控制**: 锁定特定版本，避免CDN更新导致的兼容性问题

## 维护说明

如需更新这些库的版本，请：
1. 下载新版本文件到对应目录
2. 更新本文档中的版本号
3. 测试所有相关功能确保兼容性

