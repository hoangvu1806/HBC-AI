# Bối Cảnh Công Nghệ - Trợ Lý AI HBC

## Công Nghệ Cốt Lõi

### 1. Ngôn Ngữ & Framework

-   **Python**: Ngôn ngữ lập trình chính cho toàn bộ hệ thống
-   **FastAPI**: Framework web hiệu năng cao, xây dựng trên Starlette và Pydantic
    -   Hỗ trợ tự động tạo API documentation
    -   Tích hợp validation với Pydantic
    -   Hỗ trợ async/await cho xử lý bất đồng bộ

### 2. Mô Hình Ngôn Ngữ (LLM)

-   **Tích hợp đa nhà cung cấp**:
    -   OpenAI API: Sử dụng model gpt-4o-mini mặc định
    -   Google Gemini: Tích hợp với gemini-pro
    -   Palm: Hỗ trợ text-bison-001
-   **LangChain**: Framework để xây dựng ứng dụng dựa trên LLM
    -   Chat models, callbacks, prompting
    -   Tích hợp với agents và tools
    -   Xử lý truy vấn theo chuỗi (Chain)

### 3. Cơ Sở Dữ Liệu

-   **Qdrant**: Cơ sở dữ liệu vector cho RAG
    -   Lưu trữ và tìm kiếm vector embedding
    -   Hỗ trợ tìm kiếm vector similarity
    -   Khả năng lọc metadata
-   **PostgreSQL**: Lưu trữ lịch sử chat và phiên
    -   Quản lý phiên và lịch sử trò chuyện
    -   Lưu trữ feedback từ người dùng
    -   Theo dõi sử dụng hệ thống

## Kiến Trúc Triển Khai

```
┌─────────────────────────────────────────────────────┐
│                     Ứng Dụng Client                 │
└─────────────────────────────────────────────────────┘
                            ▲
                            │
                            ▼
┌─────────────────────────────────────────────────────┐
│                 FastAPI Application Server          │
└─────────────────────────────────────────────────────┘
                ▲                     ▲
                │                     │
                ▼                     ▼
┌─────────────────────┐     ┌───────────────────────┐
│  LLM Service APIs   │     │   Vector Database     │
│  (OpenAI/Gemini)    │     │       (Qdrant)        │
└─────────────────────┘     └───────────────────────┘
                                      ▲
                                      │
                                      ▼
                        ┌───────────────────────┐
                        │    PostgreSQL DB      │
                        └───────────────────────┘
```

## Các Thư Viện Chính

### FastAPI & Web

-   **uvicorn**: ASGI server để chạy FastAPI
-   **pydantic**: Validation và serialization
-   **python-dotenv**: Quản lý biến môi trường
-   **httpx**: HTTP client cho async requests

### LangChain & LLM

-   **langchain**: Framework cho LLM applications
-   **langchain_openai**: Tích hợp với OpenAI
-   **langchain_google_genai**: Tích hợp với Google's Generative AI
-   **langchain_community**: Các tools từ cộng đồng LangChain
-   **tiktoken**: Tokenizer cho OpenAI models

### Database & Storage

-   **qdrant_client**: Client Python cho Qdrant
-   **psycopg2-binary**: PostgreSQL adapter cho Python
-   **sqlalchemy**: ORM cho tương tác database

## Yêu Cầu Môi Trường

### Phát Triển

-   Python 3.9+ (khuyến nghị Python 3.11)
-   pip hoặc conda cho quản lý package
-   Docker (không bắt buộc, nhưng được khuyến nghị)

### Production

-   Máy chủ Linux (Ubuntu 20.04+)
-   Môi trường Python 3.9+
-   Qdrant Server (phiên bản 1.0.0+)
-   PostgreSQL 13+
-   Systemd hoặc Supervisor cho quản lý process

### Biến Môi Trường

```
MODEL_NAME=gpt-4.1-mini              # Tên model LLM mặc định
TEMPERATURE=0.4                     # Độ ngẫu nhiên của model (0-1)
OPENAI_API_KEY=your_api_key         # API key cho OpenAI
GOOGLE_API_KEY=your_api_key         # API key cho Google Gemini
QDRANT_HOST=localhost               # Host của Qdrant server
QDRANT_PORT=6333                    # Port của Qdrant server
QDRANT_COLLECTION=HBC_P_HCNS_KNOWLEDGE_BASE  # Collection name
USE_POSTGRES_MEMORY=True            # Sử dụng PostgreSQL cho lưu trữ
POSTGRES_USER=postgres              # User PostgreSQL
POSTGRES_PASSWORD=postgres          # Password PostgreSQL
POSTGRES_DB=hbc_chat                # Tên database
POSTGRES_HOST=localhost             # Host PostgreSQL
POSTGRES_PORT=5432                  # Port PostgreSQL
```

## Các Kết Nối Bên Ngoài

### API Bên Ngoài

-   **OpenAI API**: Chat completions và embeddings
-   **Google Generative AI API**: Mô hình Gemini
-   **ID API**: Được sử dụng cho xác thực người dùng

### Endpoint Nội Bộ

-   **Contact Service**: Cung cấp dữ liệu liên hệ nội bộ
-   **Datetime Service**: Cung cấp ngày giờ hiện tại

## Khả Năng Mở Rộng

### Theo Chiều Ngang

-   Hỗ trợ triển khai nhiều instance qua load balancer
-   Stateless design giúp dễ dàng scale theo nhu cầu
-   Session dựa trên database giúp tránh state local

### Theo Chiều Dọc

-   Cấu hình để tận dụng nhiều core cho xử lý đồng thời
-   Tối ưu hóa database và vector search
-   Caching cho các truy vấn phổ biến

## Giới Hạn Hiện Tại

-   **Rate Limiting**: Phụ thuộc vào giới hạn từ nhà cung cấp LLM
-   **Độ Trễ**: Phản hồi có thể bị chậm khi xử lý câu hỏi phức tạp
-   **Tương Thích Dữ Liệu**: Mỗi collection Qdrant cần cấu trúc embedding cụ thể
