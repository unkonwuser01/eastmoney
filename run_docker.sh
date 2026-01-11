#!/bin/bash

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== 开始部署 EastMoney 后端服务 (Docker) ===${NC}"

# 1. 检查 Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Docker 未安装，请先安装 Docker。${NC}"
    exit 1
fi

# 检测 Compose 版本
COMPOSE_CMD=""
if docker compose version &> /dev/null; then
    COMPOSE_CMD="docker compose"
    echo "Using Docker Compose V2 (docker compose)"
elif command -v docker-compose &> /dev/null; then
    COMPOSE_CMD="docker-compose"
    echo "Using Docker Compose V1 (docker-compose)"
else
    echo -e "${RED}Docker Compose 未安装。${NC}"
    exit 1
fi

# 2. 目录准备
echo -e "${GREEN}--> 检查并创建目录结构...${NC}"
mkdir -p reports/commodities
mkdir -p reports/sentiment
mkdir -p config
mkdir -p data

# 数据库文件初始化
if [ ! -f "data/funds.db" ]; then
    if [ -d "data/funds.db" ]; then
        rm -rf data/funds.db
    fi
    touch data/funds.db
fi

# 3. 清理旧环境 (关键步骤，解决 KeyError)
echo -e "${GREEN}--> 清理旧容器和孤儿容器...${NC}"
$COMPOSE_CMD down --remove-orphans 2>/dev/null || true

# 4. 构建并启动
echo -e "${GREEN}--> 构建并启动后端容器...${NC}"
# --force-recreate 强制重新创建容器
# --build 强制重新构建镜像
$COMPOSE_CMD up -d --build --force-recreate

if [ $? -ne 0 ]; then
    echo -e "${RED}启动失败！尝试清理镜像后重试...${NC}"
    $COMPOSE_CMD down
    docker rmi eastmoney-backend:latest 2>/dev/null
    $COMPOSE_CMD up -d --build --force-recreate
fi

# 5. 状态检查
echo -e "${GREEN}--> 容器状态：${NC}"
$COMPOSE_CMD ps

echo -e "${GREEN}=== 后端服务已在端口 9000 上线 ===${NC}"
