# SmsManager 测试指南

本项目包含完整的自动化测试体系。

## 快速开始

```bash
# 安装测试依赖
cd frontend && npm install
```

## 测试命令

| 命令 | 说明 |
|------|------|
| `npm run test:api` | API 测试（无需浏览器） |
| `npm run test:browser` | 浏览器测试（Puppeteer） |
| `npm run type-check` | TypeScript 类型检查 |

## 环境要求

### API 测试
- 后端服务运行在 `http://localhost:8090`
- 或设置环境变量: `API_URL=http://your-backend`

### 浏览器测试
- 前端服务运行在 `http://localhost:5176`
- 或设置环境变量: `FRONTEND_URL=http://your-frontend`
- 后端服务运行在 `http://localhost:8090`
- 或设置环境变量: `BACKEND_URL=http://your-backend`

## 示例

```bash
# 启动服务
cd backend && nohup python -m uvicorn app.main:app --host 0.0.0.0 --port 8090 &
cd frontend && npm run dev -- --host 0.0.0.0 &

# 运行 API 测试
npm run test:api

# 运行浏览器测试
npm run test:browser
```

## CI/CD 测试

GitHub Actions 自动运行以下测试：
- API 测试
- 前端构建
- 后端 lint (ruff, black)
- 前端 lint (TypeScript)

## Docker 测试

```bash
# 使用 Docker Compose 运行完整测试
docker-compose -f docker-compose.test.yml up test
```
