# Hệ Thống Trợ Lý AI HBC

Hệ thống trợ lý AI thông minh sử dụng RAG (Retrieval-Augmented Generation) để truy xuất thông tin từ cơ sở dữ liệu tài liệu nội bộ của HBC. Hệ thống hỗ trợ nhân viên truy vấn các thông tin, quy định, quy trình và tài liệu của công ty.

## Tính Năng Chính

-   Trợ lý AI thông minh tích hợp với cơ sở dữ liệu tài liệu nội bộ
-   Hỗ trợ tra cứu thông tin từ nhiều phòng ban: HCNS, CNTT, KDTT, DVKH, v.v.
-   Streaming API cho trải nghiệm giao tiếp mượt mà
-   Hỗ trợ nhiều nhà cung cấp LLM: OpenAI, Google (Gemini)
-   Tích hợp xác thực người dùng qua ID HBC
-   Giao diện người dùng thân thiện với nhiều tính năng

## Cấu Trúc Dự Án

```
.
├── server/             # Mã nguồn backend API
├── frontend/           # Giao diện người dùng
├── tools/              # Công cụ và tiện ích
├── embedding/          # Mã nguồn xử lý và nhúng dữ liệu
├── data/               # Dữ liệu tài liệu các phòng ban
└── logs/               # File log hệ thống
```

## Yêu Cầu Hệ Thống

-   Python 3.8+
-   Node.js (cho frontend API)
-   Qdrant hoặc Postgres (Vector Database)
-   API key từ nhà cung cấp LLM (OpenAI, Google)

## Cài Đặt và Chạy

### Backend

1. Cài đặt các gói phụ thuộc:

    ```
    pip install -r requirements.txt
    ```

2. Thiết lập các biến môi trường trong file `.env`:

    ```
    OPENAI_API_KEY=your_api_key
    QDRANT_HOST=localhost
    QDRANT_PORT=6333
    MODEL_NAME=gpt-4o-mini
    TEMPERATURE=0.7
    ```

3. Khởi động server:
    ```
    cd server
    ./run_server.sh
    ```

### Frontend

1. Mở file `frontend/templates/index.html` trong trình duyệt sau khi khởi động backend.

### Tiền xử lý dữ liệu

1. Chuẩn bị dữ liệu dưới dạng PDF trong thư mục `data/`
2. Chạy script chuyển đổi PDF sang text:
    ```
    python pdf_to_txt.py
    ```
3. Tạo embedding và lưu vào vector database:
    ```
    python embedding.py
    ```

## API Endpoints

-   `POST /api/chat`: Chat với AI và nhận phản hồi đầy đủ
-   `POST /api/chat/stream`: Chat với AI và nhận phản hồi theo dạng stream
-   `GET /api/health`: Kiểm tra trạng thái hoạt động của server
-   `GET /api/config`: Lấy cấu hình hiện tại của hệ thống
-   `POST /api/provider/change`: Thay đổi nhà cung cấp LLM

## Liên Hệ

Nếu có bất kỳ câu hỏi hoặc cần hỗ trợ, vui lòng liên hệ:

-   Email: [support@hbc.com.vn](mailto:support@hbc.com.vn)
-   Phòng CNTT - Công ty Cổ phần Tập đoàn Xây dựng Hòa Bình
