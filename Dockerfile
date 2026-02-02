# ====================================
# 阶段 1: 构建前端
# ====================================
FROM node:20-alpine AS frontend-builder

WORKDIR /app/web

# 复制前端依赖文件
COPY web/package.json web/package-lock.json* ./

# 安装前端依赖
RUN npm install --registry=https://registry.npmmirror.com

# 复制前端源代码
COPY web/ ./

# 构建前端
RUN npm run build

# ====================================
# 阶段 2: 构建后端并整合前端
# ====================================
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    TZ=Asia/Shanghai \
    DB_FILE_PATH=/app/data/funds.db

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libffi-dev \
    curl \
    && ln -snf /usr/share/zoneinfo/$TZ /etc/localtime \
    && echo $TZ > /etc/timezone \
    && rm -rf /var/lib/apt/lists/*

# 复制并安装 Python 依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 复制后端代码
COPY src/ ./src/
COPY config/ ./config/
COPY app/ ./app/

# 从前端构建阶段复制构建好的静态文件
COPY --from=frontend-builder /app/web/dist ./static

# 创建必要的目录
RUN mkdir -p data reports/commodities reports/sentiment

# 暴露端口
EXPOSE 9000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:9000/api/health || exit 1

# 启动命令 - 使用 uvicorn 启动 app/main.py
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "9000"]
