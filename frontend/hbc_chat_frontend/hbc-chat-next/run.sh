#!/bin/bash

set -e  # Dừng script nếu có lỗi

IMAGE_NAME="hbc-chat-frontend:latest"
CONTAINER_NAME="hbc-chat-frontend"
DOCKERFILE="Dockerfile"
NEW_IMAGE_TAG="hbc-chat-frontend:new"
PORT=${PORT:-3030}

echo "🔍 Kiểm tra container cũ..."
if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo "✅ Container hiện tại đang chạy, giữ nguyên trong quá trình build."
else
    echo "⚠️ Không tìm thấy container cũ. Tiếp tục build image."
fi

echo "📦 Building Docker image mới..."
docker build -t $NEW_IMAGE_TAG -f $DOCKERFILE .

echo "✅ Build thành công! Chuẩn bị thay thế container cũ."

if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo "🛑 Dừng và xóa container cũ..."
    docker rm -f $CONTAINER_NAME
fi

echo "🔄 Đổi tên image mới thành latest..."
docker tag $NEW_IMAGE_TAG $IMAGE_NAME
# Xóa image tạm thời chỉ khi nó tồn tại
if docker images --format '{{.Repository}}:{{.Tag}}' | grep -q "^${NEW_IMAGE_TAG}$"; then
    docker rmi $NEW_IMAGE_TAG || true
fi

echo "🚀 Chạy container mới trên port $PORT..."
docker run -it -d --name $CONTAINER_NAME --restart always -p $PORT:$PORT $IMAGE_NAME

echo "✅ Hoàn thành! Ứng dụng đang chạy tại port $PORT"