#!/bin/bash

# Chuyển đến thư mục hiện tại của script
cd "$(dirname "$0")"

# Kiểm tra xem có cần chạy không stream
if [ "$1" = "--no-stream" ]; then
    python test_chatbot.py --no-stream
else
    python test_chatbot.py
fi 