#!/bin/bash

# Đường dẫn hiện tại
CURRENT_DIR=$(pwd)
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Chuyển đến thư mục chứa file server.py
cd $SCRIPT_DIR

# Load biến môi trường từ file .env nếu có
if [ -f ".env" ]; then
    echo "Đang load biến môi trường từ file .env"
    export $(grep -v '^#' .env | xargs)
fi

# Kiểm tra xem port đã được cung cấp qua biến môi trường chưa
if [ -z "$SERVER_PORT" ]; then
    # Nếu không, sử dụng port mặc định
    SERVER_PORT=8000
fi

# Hiển thị thông tin trước khi chạy
echo "=== THÔNG TIN SERVER ==="
echo "HOST: ${SERVER_HOST:-0.0.0.0}"
echo "PORT: $SERVER_PORT"
echo "MODEL_NAME: ${MODEL_NAME:-gpt-4o-mini}"
echo "PROVIDER: ${LLM_PROVIDER:-openai}"
echo "QDRANT_HOST: ${QDRANT_HOST:-localhost}"
echo "QDRANT_PORT: ${QDRANT_PORT:-6333}"
echo "QDRANT_COLLECTION: ${QDRANT_COLLECTION:-HBC_P_HCNS_KNOWLEDGE_BASE}"
echo "======================="

# Chạy server với uvicorn
echo "Khởi động server trên host ${SERVER_HOST:-0.0.0.0} port $SERVER_PORT..."
python3 -m uvicorn server:app --host ${SERVER_HOST:-0.0.0.0} --port $SERVER_PORT --reload

# Trở về thư mục ban đầu
cd $CURRENT_DIR 