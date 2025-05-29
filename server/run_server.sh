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

# Thiết lập môi trường
export PYTHONPATH=$PYTHONPATH:$(pwd)

# Cấu hình tối ưu hiệu năng
export SERVER_WORKERS=4                 # Số worker processes (thường bằng số CPU cores)
export MAX_CONCURRENT_REQUESTS=20       # Số request đồng thời tối đa trên mỗi worker
export UVICORN_WORKERS=4                # Số worker processes cho Uvicorn

# Số worker tối ưu thường bằng số CPU cores
CPU_CORES=$(nproc 2>/dev/null || sysctl -n hw.ncpu 2>/dev/null || echo 4)
export SERVER_WORKERS=$CPU_CORES
export UVICORN_WORKERS=$CPU_CORES

# Cấu hình database
export POSTGRES_HOST=localhost
export POSTGRES_PORT=5432
export POSTGRES_DB=chat_memory
export POSTGRES_USER=root
export POSTGRES_PASSWORD=it@HBC2025#

# Cấu hình Qdrant
export QDRANT_HOST=localhost
export QDRANT_PORT=6333
export QDRANT_COLLECTION=HBC_P_HCNS_KNOWLEDGE_BASE

# Cấu hình LLM
export MODEL_NAME=gpt-4o-mini
export TEMPERATURE=0.7
export LLM_PROVIDER=openai
export SYSTEM_PROMPT_PATH=system_prompt.md
export USE_POSTGRES_MEMORY=true

# Thông tin server
export SERVER_HOST=0.0.0.0
export SERVER_PORT=8000

# Kiểm tra cài đặt Python packages
echo "Kiểm tra cài đặt packages..."
pip install -q fastapi uvicorn python-dotenv httpx

echo "Khởi động server FastAPI với $UVICORN_WORKERS workers và $MAX_CONCURRENT_REQUESTS concurrent requests mỗi worker"
# Kiểm tra và sử dụng Python từ conda nếu có
if [ -n "$CONDA_PREFIX" ]; then
    echo "Sử dụng Python từ conda: $CONDA_PREFIX/bin/python"
    $CONDA_PREFIX/bin/python -m uvicorn server:app --host $SERVER_HOST --port $SERVER_PORT --workers $UVICORN_WORKERS
else
    # Thử sử dụng python3 nếu không có conda
    if command -v python3 &> /dev/null; then
        echo "Sử dụng Python3"
        python3 -m uvicorn server:app --host $SERVER_HOST --port $SERVER_PORT --workers $UVICORN_WORKERS
    else
        # Fallback về python
        echo "Sử dụng Python mặc định"
        python -m uvicorn server:app --host $SERVER_HOST --port $SERVER_PORT --workers $UVICORN_WORKERS
    fi
fi

# Trở về thư mục ban đầu
cd $CURRENT_DIR 