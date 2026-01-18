#!/bin/bash

# 构建和部署脚本

set -e

IMAGE_NAME="eastmoney-app"
IMAGE_TAG="latest"
CONTAINER_NAME="eastmoney-container"
PORT="9000"

echo "🚀 开始构建 Docker 镜像..."
docker build --network=host -t ${IMAGE_NAME}:${IMAGE_TAG} .

echo "✅ 镜像构建完成!"

echo "🛑 停止并删除旧容器..."
docker stop ${CONTAINER_NAME} 2>/dev/null || true
docker rm ${CONTAINER_NAME} 2>/dev/null || true

echo "🎯 启动新容器..."
docker run -d \
  --name ${CONTAINER_NAME} \
  --network host \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/reports:/app/reports \
  -v $(pwd)/config:/app/config \
  -v $(pwd)/.env:/app/.env \
  -e TZ=Asia/Shanghai \
  -e DB_FILE_PATH=/app/data/funds.db \
  --restart unless-stopped \
  ${IMAGE_NAME}:${IMAGE_TAG}

echo "✅ 容器已启动!"
echo "📍 访问地址: http://localhost:${PORT}"
echo ""
echo "📊 查看日志: docker logs -f ${CONTAINER_NAME}"
echo "🔍 查看状态: docker ps | grep ${CONTAINER_NAME}"
