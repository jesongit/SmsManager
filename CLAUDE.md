# SmsManager - 局域网设备管理系统

轻量化的 SmsForwarder 远程控制 Web 管理界面。

## 项目概述

- **后端**: FastAPI + SQLite
- **前端**: Vue 3 + Naive UI + TypeScript
- **认证**: JWT + TOTP 2FA
- **设备通信**: 对接 SmsForwarder API (v2/v3)

## 默认账号

- **用户名**: `admin`
- **密码**: `admin`

## 项目结构

```
SmsManager/
├── backend/                 # FastAPI 后端
│   ├── app/
│   │   ├── api/            # API 路由
│   │   │   ├── auth.py     # 认证接口
│   │   │   └── devices.py  # 设备管理
│   │   ├── models/         # 数据库模型
│   │   │   ├── user.py
│   │   │   └── device.py
│   │   ├── schemas/        # Pydantic 模式
│   │   │   ├── user.py
│   │   │   ├── device.py
│   │   │   └── sf.py       # SmsForwarder API 模式
│   │   ├── services/       # 业务逻辑
│   │   │   └── sf_service.py  # SmsForwarder 客户端
│   │   ├── utils/          # 工具函数
│   │   │   ├── auth.py     # JWT/密码
│   │   │   ├── totp.py     # 2FA
│   │   │   └── network.py  # ARP 扫描 + 端口探测
│   │   ├── main.py         # 应用入口
│   │   ├── config.py       # 配置
│   │   └── database.py     # SQLite
│   ├── requirements.txt
│   └── tests/
│
├── frontend/                # Vue 3 前端
│   ├── src/
│   │   ├── api/            # API 封装
│   │   ├── stores/         # Pinia 状态
│   │   ├── views/          # 页面
│   │   │   ├── Home.vue    # 首页 (设备列表/扫描/添加)
│   │   │   ├── Device.vue  # 设备详情
│   │   │   ├── Profile.vue # 用户中心
│   │   │   └── Login.vue   # 登录
│   │   ├── router/         # 路由
│   │   └── main.ts
│   ├── package.json
│   └── vite.config.ts
│
└── CLAUDE.md               # 项目文档 (重要!)
```

## 快速开始

### 端口规划

| 服务 | 端口 | 说明 |
|------|------|------|
| 后端 API | `8090` | FastAPI 服务 |
| 前端页面 | `5173` | Vite 开发服务器 |

> **注意**: 每次启动前先清理旧进程
> ```bash
> # 清理占用端口的进程
> lsof -i :8090 2>/dev/null | grep -v COMMAND | awk '{print $2}' | xargs -r kill -9 2>/dev/null
> lsof -i :5173 2>/dev/null | grep -v COMMAND | awk '{print $2}' | xargs -r kill -9 2>/dev/null
> ```

### 启动命令

**方式一：手动启动（推荐用于开发调试）**

```bash
# 终端 1 - 启动后端 (8090)
cd backend
nohup python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8090 > /tmp/backend.log 2>&1 &

# 终端 2 - 启动前端 (5173)
cd frontend
nohup npm run dev -- --port 5173 > /tmp/frontend.log 2>&1 &
```

**方式二：一键启动脚本**

```bash
cd /root/code/SmsManager

# 启动后端
cd backend && nohup python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8090 > /tmp/backend.log 2>&1 &

# 启动前端 (在另一个终端或等待后端启动后)
cd frontend && nohup npm run dev -- --port 5173 > /tmp/frontend.log 2>&1 &
```

### 验证服务状态

```bash
# 后端健康检查
curl http://localhost:8090/health
# 期望返回: {"status":"healthy","app":"SmsManager"}

# 前端页面
curl http://localhost:5173
# 期望返回: HTML 页面
```

### 停止服务

```bash
# 杀掉端口进程
lsof -i :8090 | grep -v COMMAND | awk '{print $2}' | xargs -r kill -9
lsof -i :5173 | grep -v COMMAND | awk '{print $2}' | xargs -r kill -9
```

### 快速重启

```bash
# 停止后重启
lsof -i :8090 | grep -v COMMAND | awk '{print $2}' | xargs -r kill -9
lsof -i :5173 | grep -v COMMAND | awk '{print $2}' | xargs -r kill -9
sleep 1

cd backend && nohup python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8090 > /tmp/backend.log 2>&1 &
cd frontend && nohup npm run dev -- --port 5173 > /tmp/frontend.log 2>&1 &
sleep 3

# 验证
curl http://localhost:8090/health
curl http://localhost:5173 | head -1
```

### 查看日志

```bash
# 后端日志
cat /tmp/backend.log

# 前端日志
cat /tmp/frontend.log
```

---

**访问地址**:
- 🌐 前端: http://localhost:5173
- 📡 API: http://localhost:8090
- 📖 API 文档: http://localhost:8090/docs

## API 接口文档

### 基础信息

- **Base URL**: `http://localhost:8090` (后端)
- **认证**: Bearer Token (JWT)
- **Content-Type**: `application/json`

---

### 认证接口 `/api/auth`

| 方法 | 路径 | 描述 | 请求体 | 响应 |
|------|------|------|--------|------|
| POST | `/api/auth/login` | 登录获取 Token | `username`, `password`, `totp_code`(可选) | `{access_token, token_type}` |
| POST | `/api/auth/logout` | 退出登录 | - | `{message}` |
| GET | `/api/auth/me` | 获取当前用户 | Headers: `Authorization: Bearer <token>` | UserResponse |
| PUT | `/api/auth/me` | 更新用户信息 | `username`, `avatar` | UserResponse |
| PUT | `/api/auth/password` | 修改密码 | `old_password`, `new_password` | `{message}` |
| GET | `/api/auth/2fa/status` | 获取 2FA 状态 | Headers: `Authorization` | `{enabled, secret_set}` |
| POST | `/api/auth/2fa/setup` | 设置 2FA | Headers: `Authorization` | `{secret, qr_code}` |
| POST | `/api/auth/2fa/verify` | 验证并启用 2FA | `code` | `{message}` |
| POST | `/api/auth/2fa/disable` | 禁用 2FA | `code` | `{message}` |

**注意**: 注册功能已移除，只有默认 admin 用户。

---

### 设备接口 `/api/devices`

| 方法 | 路径 | 描述 | 请求参数/体 |
|------|------|------|-------------|
| GET | `/api/devices` | 获取设备列表 | `skip`, `limit` (query) |
| GET | `/api/devices/{id}` | 获取设备详情 | - |
| POST | `/api/devices` | 添加设备 | DeviceCreate |
| PUT | `/api/devices/{id}` | 更新设备 | DeviceUpdate |
| DELETE | `/api/devices/{id}` | 删除设备 | - |
| **POST** | **`/api/devices/scan`** | **扫描局域网** | **无参数** |
| POST | `/api/devices/test/{id}` | 测试设备连接 | - |

#### 扫描接口详情 `/api/devices/scan`

**重要**: 这是扫描局域网的接口。

**扫描策略**:
- **扫描端口**: `5000` (SmsForwarder), `80` (HTTP), `443` (HTTPS), `8080` (备用 Web)
- **并发数**: 200
- **超时**: 0.1 秒/端口
- **扫描范围**: `192.168.x.1-50` (只扫描前 50 个 IP)

**返回格式**:
```json
{
  "local_ip": "192.168.31.20",
  "gateway_ip": "192.168.31.1",
  "arp_devices": [
    {"ip": "192.168.31.1", "mac": "a4:a9:30:8d:49:c7", "hostname": "xiaoqiang", "source": "arp"}
  ],
  "scanned_devices": [
    {
      "ip": "192.168.31.10",
      "hostname": "homeassistant",
      "port": 80,
      "is_smsforwarder": false,
      "response_time": 150.5
    }
  ],
  "total_arp": 1,
  "total_scanned": 1,
  "message": "ARP: 1 个, 扫描: 1 个设备"
}
```

**过滤规则**:
- 自动过滤 `169.254.x.x` (链路本地地址)
- 自动过滤 `100.x.x.x` (保留地址)
- 只保留有效局域网 IP

---

### SmsForwarder 设备操作接口

以下接口需要 `{device_id}` 和认证 Header。

#### 短信操作

| 方法 | 路径 | 请求体 |
|------|------|--------|
| POST | `/api/devices/{id}/sms/send` | `{sim_slot, phone_numbers, msg_content}` |
| POST | `/api/devices/{id}/sms/query` | `{type, page_num, page_size, keyword?}` |

#### 通话记录

| 方法 | 路径 | 请求体 |
|------|------|--------|
| POST | `/api/devices/{id}/call/query` | `{type, page_num, page_size, phone_number?}` |

#### 联系人

| 方法 | 路径 | 请求体 |
|------|------|--------|
| POST | `/api/devices/{id}/contact/query` | `{phone_number?, name?}` |
| POST | `/api/devices/{id}/contact/add` | `{phone_number, name?}` |

#### 设备状态

| 方法 | 路径 |
|------|------|
| POST | `/api/devices/{id}/battery` |
| POST | `/api/devices/{id}/location` |

#### Wake on LAN

| 方法 | 路径 | 请求体 |
|------|------|--------|
| POST | `/api/devices/{id}/wol` | `{mac, ip?, port?}` |

#### 配置管理

| 方法 | 路径 | 请求体 |
|------|------|--------|
| POST | `/api/devices/{id}/config` | - |
| POST | `/api/devices/{id}/clone/pull` | `{version_code}` |

---

## 扫描逻辑说明

### 当前扫描配置

| 配置项 | 值 | 说明 |
|--------|-----|------|
| 扫描端口 | `5000` | SmsForwarder 默认端口 |
| 并发数 | `100` | 并发扫描的 IP 数量 |
| 超时 | `0.5` 秒 | 单个端口连接超时 |
| 扫描范围 | `192.168.x.1-254` | 整个 /24 网段 |

### 为什么扫描不到设备？

1. **设备不在同一网段**: 确保设备和电脑在同一 WiFi
2. **端口不对**: SmsForwarder 默认端口是 5000，可在设置查看
3. **防火墙**: 部分设备可能阻止外部连接
4. **超时太短**: 默认 0.5 秒，普通网络足够

### 扫描速度

- **预计耗时**: 约 120 秒 (254 个 IP × 0.5 秒超时)
- **找到设备数**: 根据实际情况，通常 1-10 个

### 常见问题排查

```bash
# 1. 测试特定 IP 是否可达
curl http://设备IP:5000

# 2. 检查本地 IP
ip addr show | grep inet

# 3. 查看 ARP 缓存
cat /proc/net/arp
```

### 性能调优

如需调整扫描参数，修改 `backend/app/utils/network.py`:
```python
SCAN_PORTS = [5000]       # 扫描端口列表
SCAN_CONCURRENCY = 100    # 并发数 (越大越快但可能丢包)
SCAN_TIMEOUT = 0.5         # 超时秒数 (慢设备需要更长)
SCAN_RANGE = 254           # 扫描 IP 数量 (1-254)
```

## SmsForwarder API 对接

### 支持的 API 版本

- v2.4.4 及以下版本
- v3.0.0+ 版本 (推荐)

### 支持的功能

| 功能 | API 端点 |
|------|----------|
| 配置查询 | `/config/query` |
| 短信发送 | `/sms/send` |
| 短信查询 | `/sms/query` |
| 通话记录 | `/call/query` |
| 话簿管理 | `/contact/query`, `/contact/add` |
| 电池状态 | `/battery/query` |
| 设备定位 | `/location/query` |
| 远程唤醒 | `/wol/send` |
| 一键换机 | `/clone/pull`, `/clone/push` |

## 技术栈版本

### 后端

- Python 3.10+
- FastAPI 0.109+
- SQLAlchemy 2.0+
- Pydantic 2.5+
- JWT (python-jose)
- TOTP (pyotp)

### 前端

- Vue 3.4+
- TypeScript 5.3+
- Vite 5.1+
- Naive UI 2.38+
- Pinia 2.1+
- Vue Router 4.2+

## 开发规范

### 后端

- 使用 Pydantic 模型验证请求/响应
- 使用 SQLAlchemy ORM 操作数据库
- API 路由返回 Pydantic 模式
- 所有路由需认证（除非标记为 `public`）

### 前端

- TypeScript 严格模式
- 组件使用 `<script setup>` 语法
- API 调用封装在 `src/api/` 目录
- 状态管理使用 Pinia
- UI 使用 Naive UI 组件库

## 测试

```bash
# API 测试 (无需浏览器)
cd frontend
npm run test:api

# 浏览器测试 (需要前端运行)
npm run test:browser

# 类型检查
npm run type-check
```

---

## Docker 部署

### 生产环境（推荐）

生产环境只需启动后端，它会自动服务前端静态文件。

**步骤：**

```bash
# 1. 确保已构建前端
cd frontend
npm run build

# 2. 构建并启动 Docker 容器
cd /root/code/SmsManager
docker compose -f docker-compose.prod.yml up -d --build

# 3. 查看日志
docker compose -f docker-compose.prod.yml logs -f

# 4. 停止服务
docker compose -f docker-compose.prod.yml down
```

**访问地址：** http://localhost:8090

**数据持久化：** 数据库保存在 Docker volume `sms_data` 中

---

### 🚀 快速更新方案（避免长时间编译）

Docker 完整重建需要 5-10 分钟（安装系统依赖 + Python 包），以下方案可加速更新：

#### 场景 1：只修改前端代码

```bash
# 1. 构建前端
cd frontend
npm run build

# 2. 复制到容器（不重建镜像）
docker cp frontend/dist/. sms-manager:/app/frontend/dist/

# 3. 重启容器
docker restart sms-manager
```
**耗时：** 10-30 秒

#### 场景 2：只修改后端 Python 代码

```bash
# 1. 复制后端代码到容器
docker cp backend/app/. sms-manager:/app/app/

# 2. 重启容器
docker restart sms-manager
```
**耗时：** 5-10 秒

#### 场景 3：前后端都修改

```bash
# 1. 构建前端
cd frontend
npm run build

# 2. 复制前后端代码
docker cp frontend/dist/. sms-manager:/app/frontend/dist/
docker cp backend/app/. sms-manager:/app/app/

# 3. 重启容器
docker restart sms-manager
```
**耗时：** 30-60 秒

#### 场景 4：必须完整重建镜像的情况

- 修改了 `requirements.txt`（新增 Python 依赖）
- 修改了 `Dockerfile`
- 修改了系统级配置

```bash
# 完整重建（需要 5-10 分钟）
cd /root/code/SmsManager
docker compose -f docker-compose.prod.yml down
docker compose -f docker-compose.prod.yml build --no-cache
docker compose -f docker-compose.prod.yml up -d
```

---

### Docker 命令速查

```bash
# 启动
docker compose -f docker-compose.prod.yml up -d

# 停止
docker compose -f docker-compose.prod.yml down

# 重启
docker compose -f docker-compose.prod.yml restart

# 查看日志
docker compose -f docker-compose.prod.yml logs -f

# 进入容器
docker exec -it sms-manager /bin/bash

# 查看容器状态
docker ps | grep sms
```

---

### 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `DATABASE_PATH` | 数据库文件路径 | `/app/backend/data/sqlite.db` |
| `JWT_SECRET_KEY` | JWT 密钥 | `your-secret-key-change-in-production` |
| `TZ` | 时区 | `Asia/Shanghai` |

---

## 重要提醒

1. **注册已移除**: 只有默认 admin 用户
2. **2FA 可选**: 默认关闭，可在用户中心启用
3. **扫描端口**: 记住扫描的是 `5000, 80, 443, 8080`
4. **过滤无效 IP**: 169.254.x.x 和 100.x.x.x 会被自动过滤
5. **不要使用 playwright**: WSL 环境下 playwright 的 chrome 沙箱有问题，测试 API 用 curl 命令即可
6. 每次新增或者修改完功能，完整测试一遍前后端再通知完成,并且总结告诉我你做了什么
7. 不要随便往 CLAUDE.md 添加东西，除非我让你记住的
