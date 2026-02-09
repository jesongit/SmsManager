# ========================
# 第一阶段：构建前端
# ========================
FROM docker.1ms.run/node:20-alpine AS frontend-builder

# 配置 npm 源为阿里云镜像
RUN npm config set registry https://registry.npmmirror.com/

# 设置工作目录
WORKDIR /app

# 复制前端依赖文件
COPY frontend/package.json frontend/package-lock.json* ./

# 安装前端依赖
RUN npm ci

# 复制前端源代码
COPY frontend/ .

# 构建前端
RUN npm run build

# ========================
# 第二阶段：运行后端
# ========================
FROM docker.1ms.run/python:3.13-slim

# 配置 apt 源为阿里云镜像（阿里云 Debian 镜像站）
RUN sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list.d/debian.sources 2>/dev/null || \
    sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list 2>/dev/null || true

# 安装系统依赖（包括构建 netifaces 所需的依赖）
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    iproute2 \
    gcc \
    g++ \
    make \
    libc-dev \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# 设置工作目录
WORKDIR /app

# 创建数据目录
RUN mkdir -p /app/data

# 配置 pip 源为阿里云镜像
RUN pip config set global.index-url https://mirrors.aliyun.com/pypi/simple/

# 复制 Python 依赖文件
COPY backend/requirements.txt /app/requirements.txt

# 安装 Python 依赖
RUN pip install --no-cache-dir -r /app/requirements.txt

# 复制后端代码
COPY backend/app/ /app/app/

# 从第一阶段复制前端构建产物
COPY --from=frontend-builder /app/dist /app/frontend/dist

# 设置环境变量
ENV DATABASE_PATH=/app/data/sqlite.db

# 暴露端口
EXPOSE 8090

# 启动命令
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8090"]
