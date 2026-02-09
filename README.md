# SmsManager - SmsForwarder Web 管理平台

<div align="center">

[![GitHub stars](https://img.shields.io/github/stars/yourusername/SmsManager?style=flat-square)](https://github.com/yourusername/SmsManager/stargazers)
[![GitHub issues](https://img.shields.io/github/issues/yourusername/SmsManager?style=flat-square)](https://github.com/yourusername/SmsManager/issues)
[![Docker Pulls](https://img.shields.io/docker/pulls/yourusername/sms-manager?style=flat-square)](https://hub.docker.com/r/yourusername/sms-manager)

一个基于 Web 的 SmsForwarder 设备管理平台，支持多设备管理、局域网自动发现、API 对接等功能。

</div>

## ✨ 功能特性

- 🔐 **安全认证**：支持用户名密码登录 + TOTP 双因素认证
- 📱 **设备管理**：添加、编辑、删除 SmsForwarder 设备
- 🔍 **自动发现**：局域网扫描，自动识别 SmsForwarder 设备
- 📊 **状态监控**：实时查看设备在线状态
- 🎨 **精美界面**：基于 Naive UI 的现代化 Web UI
- 🐳 **Docker 部署**：开箱即用的 Docker 部署方案
- 🔄 **多设备支持**：同时管理多个 SmsForwarder 设备

## 🏗️ 技术栈

### 后端

| 技术 | 用途 |
|------|------|
| **Python 3.13** | 运行时 |
| **FastAPI** | Web 框架 |
| **SQLAlchemy** | ORM |
| **SQLite** | 数据库 |
| **JWT** | Token 认证 |
| **TOTP** | 双因素认证 |

### 前端

| 技术 | 用途 |
|------|------|
| **Vue 3** | 框架 |
| **TypeScript** | 类型安全 |
| **Naive UI** | 组件库 |
| **Pinia** | 状态管理 |
| **Vue Router** | 路由 |
| **Axios** | HTTP 客户端 |

## 📁 项目结构

```
SmsManager/
├── backend/                 # FastAPI 后端
│   ├── app/
│   │   ├── api/           # API 路由
│   │   │   ├── auth.py    # 认证接口
│   │   │   └── devices.py  # 设备接口
│   │   ├── models/        # 数据模型
│   │   ├── schemas/       # Pydantic 模型
│   │   ├── services/      # 业务逻辑
│   │   └── utils/         # 工具函数
│   ├── data/              # 数据库存储
│   ├── requirements.txt   # Python 依赖
│   └── tests/             # 测试文件
│
├── frontend/               # Vue 3 前端
│   ├── src/
│   │   ├── api/          # API 封装
│   │   ├── stores/       # Pinia 状态
│   │   ├── views/        # 页面组件
│   │   ├── router/       # 路由配置
│   │   └── assets/       # 静态资源
│   ├── dist/             # 构建产物
│   ├── package.json      # NPM 配置
│   └── vite.config.ts    # Vite 配置
│
├── Dockerfile             # Docker 构建
├── docker-compose.prod.yml # 生产部署
├── docker-compose.test.yml # 测试部署
└── README.md             # 本文档
```

## 🚀 快速开始

### 方式一：Docker 部署（推荐）

```bash
# 1. 克隆项目
git clone https://github.com/yourusername/SmsManager.git
cd SmsManager

# 2. 构建并启动
docker compose -f docker-compose.prod.yml up -d

# 3. 访问服务
# http://localhost:8090
```

### 方式二：本地开发

```bash
# 1. 克隆项目
git clone https://github.com/yourusername/SmsManager.git
cd SmsManager

# 2. 后端设置
cd backend
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 启动后端
uvicorn app.main:app --host 0.0.0.0 --port 8090 --reload

# 3. 前端设置（新建终端）
cd frontend
npm install

# 启动开发服务器
npm run dev

# 4. 访问
# 后端: http://localhost:8090
# 前端: http://localhost:5173
```

## 🔧 配置说明

### 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `DATABASE_PATH` | 数据库路径 | `/app/data/sqlite.db` |
| `TZ` | 时区 | `Asia/Shanghai` |

### 端口说明

| 端口 | 服务 | 说明 |
|------|------|------|
| `8090` | 主服务 | Web 界面 + API |

## 📡 API 文档

### 认证接口

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/auth/register` | 用户注册 |
| POST | `/api/auth/login` | 用户登录 |
| POST | `/api/auth/logout` | 登出 |
| POST | `/api/auth/2fa/setup` | 设置 2FA |
| POST | `/api/auth/2fa/verify` | 验证 2FA |

### 设备接口

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/devices` | 获取设备列表 |
| POST | `/api/devices` | 添加设备 |
| GET | `/api/devices/{id}` | 获取设备详情 |
| PUT | `/api/devices/{id}` | 更新设备 |
| DELETE | `/api/devices/{id}` | 删除设备 |
| POST | `/api/devices/scan` | 扫描局域网设备 |
| GET | `/api/devices/{id}/status` | 获取设备状态 |
| GET | `/api/devices/{id}/sms` | 获取短信列表 |
| POST | `/api/devices/{id}/sms/send` | 发送短信 |

### 用户接口

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/user/profile` | 获取用户信息 |
| PUT | `/api/user/profile` | 更新用户信息 |
| PUT | `/api/user/password` | 修改密码 |

详细 API 文档请访问：`http://localhost:8090/docs`（启动服务后）

## 🐳 Docker 部署说明

### 生产环境

```bash
# 构建镜像
docker build -t sms-manager:latest .

# 运行容器
docker run -d \
  --name sms-manager \
  -p 8090:8090 \
  -v $(pwd)/data:/app/data \
  -e TZ=Asia/Shanghai \
  sms-manager:latest
```

### 使用 Docker Compose

```bash
# 启动
docker compose -f docker-compose.prod.yml up -d

# 查看日志
docker compose -f docker-compose.prod.yml logs -f

# 停止
docker compose -f docker-compose.prod.yml down
```

## 🧪 测试

```bash
# 运行所有测试
./test-all.sh

# 运行后端测试
./run-tests.sh

# 查看测试报告
# backend/tests/report.html
```

## 📝 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件。

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

## 📧 联系

如有问题，请通过 [Issue](https://github.com/yourusername/SmsManager/issues) 反馈。

---

<div align="center">

Made with ❤️ by Posase

</div>
