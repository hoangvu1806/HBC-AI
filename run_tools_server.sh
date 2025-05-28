#!/bin/bash

# Đường dẫn đến môi trường ảo (nếu sử dụng)
VENV_PATH="venv"
SERVER_PORT=8001  # Thay đổi port sang 8001 để tránh vấn đề quyền

# Kiểm tra và kích hoạt môi trường ảo nếu tồn tại
if [ -d "$VENV_PATH" ]; then
    echo "Kích hoạt môi trường ảo..."
    source "$VENV_PATH/bin/activate"
fi

# Kiểm tra các biến môi trường cần thiết
if [ -z "$QDRANT_HOST" ]; then
    export QDRANT_HOST="localhost"
fi

if [ -z "$QDRANT_PORT" ]; then
    export QDRANT_PORT=6333
fi

if [ -z "$COLLECTION_NAME" ]; then
    export COLLECTION_NAME="HBC_P_HCNS_KNOWLEDGE_BASE"
fi

# Tạo thư mục logs nếu chưa tồn tại
mkdir -p logs

# Kiểm tra xem server có đang chạy không
if pgrep -f "uvicorn tools.tools_server:app" > /dev/null; then
    echo "Server đang chạy. Dừng server cũ..."
    pkill -f "uvicorn tools.tools_server:app"
    sleep 2
fi

# Chạy server với log định hướng vào thư mục logs
echo "Khởi động Tools Server trên port $SERVER_PORT..."
cd .. # Di chuyển lên thư mục gốc để uvicorn có thể tìm thấy module tools

 --log-level info > logs/tools_server.log 2>&1

# Xử lý khi dừng script
trap 'echo "Dừng server..."; pkill -f "uvicorn tools.tools_server:app"' SIGINT SIGTERM 