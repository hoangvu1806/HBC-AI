# Server API Trợ Lý AI HBC

Thành phần backend của hệ thống Trợ Lý AI HBC, cung cấp API để tương tác với mô hình ngôn ngữ lớn (LLM) và hệ thống RAG (Retrieval-Augmented Generation).

## Cấu Trúc Thư Mục

```
server/
├── __init__.py             # Module initialization
├── agent_creator.py        # Tạo Agent tùy chỉnh
├── agent_tools.py          # Công cụ cho agent
├── chat_memory.py          # Quản lý bộ nhớ cuộc trò chuyện
├── chat_with_RAG.py        # Xử lý trò chuyện với RAG
├── db_models.py            # Mô hình dữ liệu
├── db_repository.py        # Giao tiếp với cơ sở dữ liệu
├── model.py                # Định nghĩa mô hình LLM
├── server.py               # FastAPI server
├── system_prompt.md        # Nhắc hệ thống cho LLM
├── test/                   # Thư mục test
├── test_chatbot.py         # Test chatbot
├── run_server.sh           # Script chạy server
└── run_test_chatbot.sh     # Script test chatbot
```

## API Endpoints

### Chat API

-   `POST /api/chat`: Chat với AI và nhận phản hồi đầy đủ

    -   Tham số: `topic`, `prompt`, `section_name`, `think`
    -   Phản hồi: `ChatResponse` (output, tool_usages, topic, section_name, think)

-   `POST /api/chat/stream`: Chat với AI và nhận phản hồi theo dạng stream

    -   Tham số: Giống như /api/chat
    -   Phản hồi: Server-Sent Events (SSE)

-   `POST /api/chat/clear`: Xóa lịch sử trò chuyện
    -   Phản hồi: Trạng thái thành công

### Quản Lý API

-   `GET /api/health`: Kiểm tra trạng thái server

    -   Phản hồi: `{"status": "ok", "provider": [nhà cung cấp hiện tại]}`

-   `GET /api/config`: Lấy cấu hình hiện tại

    -   Phản hồi: Thông tin cấu hình hệ thống

-   `POST /api/provider/change`: Thay đổi nhà cung cấp LLM
    -   Tham số: `provider` (openai, gemini, palm)
    -   Phản hồi: Trạng thái thành công/thất bại

### Khởi Tạo Phiên Trò Chuyện

-   `POST /api/chat/init`: Khởi tạo phiên trò chuyện mới
    -   Tham số: `session_name`, `email`, `expertor`
    -   Phản hồi: ID phiên và thông tin trạng thái

## Cách Sử Dụng

### Cài Đặt Môi Trường

1. Cài đặt các thư viện phụ thuộc:

    ```bash
    pip install fastapi uvicorn openai langchain langchain-openai qdrant-client python-dotenv
    ```

2. Tạo file `.env` với các biến môi trường cần thiết:
    ```
    MODEL_NAME=gpt-4o-mini
    TEMPERATURE=0.7
    OPENAI_API_KEY=your_openai_api_key
    GOOGLE_API_KEY=your_gemini_api_key
    QDRANT_HOST=localhost
    QDRANT_PORT=6333
    QDRANT_COLLECTION=HBC_P_HCNS_KNOWLEDGE_BASE
    USE_POSTGRES_MEMORY=True
    ```

### Chạy Server

Sử dụng script `run_server.sh`:

```bash
./run_server.sh
```

Hoặc chạy trực tiếp với uvicorn:

```bash
uvicorn server:app --host 0.0.0.0 --port 8000 --reload
```

### Test API

Sử dụng script `run_test_chatbot.sh` để kiểm tra hoạt động của chatbot:

```bash
./run_test_chatbot.sh
```

## Kiến Trúc Hệ Thống

Server sử dụng kiến trúc RAG (Retrieval-Augmented Generation):

1. Nhận câu hỏi từ người dùng
2. Truy xuất thông tin liên quan từ cơ sở dữ liệu vector (Qdrant)
3. Kết hợp thông tin truy xuất với câu hỏi để tạo ngữ cảnh cho LLM
4. Gửi prompt đến LLM và trả về kết quả

## Cấu Hình Nâng Cao

-   Điều chỉnh các tham số trong file `.env` để tối ưu hiệu suất
-   Chỉnh sửa `system_prompt.md` để thay đổi hành vi của trợ lý AI
-   Tùy chỉnh các công cụ trong `agent_tools.py` để thêm chức năng mới

## Liên Hệ

Nếu có vấn đề hoặc câu hỏi về API, vui lòng liên hệ phòng CNTT.
