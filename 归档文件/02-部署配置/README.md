# 部署配置文件说明

本目录存放部署相关的配置文件。

## 📄 文件列表

### vercel.json
- **用途**：Vercel平台部署配置文件
- **内容**：URL重写规则，将所有请求重定向到index.html（适用于单页应用）
- **说明**：如果项目不需要部署到Vercel平台，可以归档此文件
- **是否可以删除**：⚠️ 视情况而定
  - 如果不需要部署到Vercel：✅ 可以删除
  - 如果需要部署到Vercel：❌ 需要保留在项目根目录

### .vercelignore
- **用途**：Vercel部署忽略规则文件
- **内容**：指定Vercel部署时忽略的文件和目录
- **说明**：如果项目不需要部署到Vercel平台，可以归档此文件
- **是否可以删除**：⚠️ 视情况而定
  - 如果不需要部署到Vercel：✅ 可以删除
  - 如果需要部署到Vercel：❌ 需要保留在项目根目录

## 🔄 恢复方法

如果需要部署到Vercel，可以将这些文件移回项目根目录：

```bash
# 恢复Vercel配置文件
mv 归档文件/02-部署配置/vercel.json .
mv 归档文件/02-部署配置/.vercelignore .
```

## 📝 其他部署平台

如果使用其他部署平台（如Heroku、AWS、Azure等），需要创建对应的配置文件：
- Heroku: `Procfile`, `runtime.txt`
- AWS: `serverless.yml`, `Dockerfile`
- Azure: `web.config`, `requirements.txt`

## ⚠️ 注意事项

- 这些文件只在需要部署到Vercel时才需要
- 如果项目只在本机或内网运行，可以归档这些文件
- 删除前请确认不需要Vercel部署功能
