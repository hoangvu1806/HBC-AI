# Kiến Trúc Hệ Thống và Mẫu Thiết Kế - Trợ Lý AI HBC

## Tổng Quan Kiến Trúc

Hệ thống Trợ Lý AI HBC được thiết kế theo kiến trúc module hóa, tách biệt các thành phần chức năng để dễ dàng bảo trì và mở rộng. Kiến trúc tổng thể được xây dựng dựa trên các nguyên tắc thiết kế hiện đại và các mẫu phát triển phần mềm phổ biến.

```
┌─────────────────┐         ┌───────────────────┐         ┌───────────────┐
│    FastAPI      │         │     RAG Agent     │         │    Vector DB  │
│    Server       │◄────────┤(LLM + Retrieval)  │◄────────┤   (Qdrant)    │
└─────────────────┘         └───────────────────┘         └───────────────┘
        ▲                             ▲                           ▲
        │                             │                           │
        ▼                             ▼                           ▼
┌─────────────────┐         ┌───────────────────┐         ┌───────────────┐
│ Authentication  │         │   Agent Tools     │         │ PostgreSQL DB │
│    Module       │         │                   │         │ (Chat Memory) │
└─────────────────┘         └───────────────────┘         └───────────────┘
```

## Mô Hình Thành Phần Chính

### 1. Module Server (server.py)

-   **Mẫu thiết kế**: Front Controller Pattern
-   **Trách nhiệm**:
    -   Khởi tạo và cấu hình FastAPI server
    -   Định nghĩa các API endpoint
    -   Xử lý yêu cầu từ client
    -   Điều phối luồng dữ liệu
-   **Tương tác**: Giao tiếp với RAGAgent để xử lý yêu cầu chat

### 2. Module RAG Agent (chat_with_RAG.py)

-   **Mẫu thiết kế**: Mediator Pattern, Strategy Pattern
-   **Trách nhiệm**:
    -   Điều phối việc truy xuất thông tin và sinh câu trả lời
    -   Tích hợp mô hình ngôn ngữ (LLM) và cơ sở dữ liệu vector
    -   Tạo và quản lý các agent (normal, think mode)
-   **Tương tác**: Gọi các công cụ (tools) và LLM để tạo câu trả lời

### 3. Module LLM (model.py)

-   **Mẫu thiết kế**: Factory Pattern, Adapter Pattern
-   **Trách nhiệm**:
    -   Khởi tạo và quản lý tương tác với mô hình ngôn ngữ lớn
    -   Hỗ trợ nhiều nhà cung cấp khác nhau (OpenAI, Gemini, Palm)
    -   Xử lý prompt và phản hồi
    -   Tính toán embedding cho văn bản
-   **Tương tác**: Giao tiếp với API của các nhà cung cấp LLM

### 4. Module Agent Tools (agent_tools.py)

-   **Mẫu thiết kế**: Command Pattern
-   **Trách nhiệm**:
    -   Cung cấp các công cụ (tools) cho agent sử dụng
    -   Theo dõi và ghi log việc sử dụng công cụ
    -   Định nghĩa các hàm truy xuất dữ liệu cụ thể
-   **Tương tác**: Kết nối với Qdrant để tìm kiếm dữ liệu

### 5. Module Bộ Nhớ Trò Chuyện (chat_memory.py)

-   **Mẫu thiết kế**: Repository Pattern
-   **Trách nhiệm**:
    -   Lưu trữ và truy xuất lịch sử trò chuyện
    -   Quản lý phiên trò chuyện
    -   Hỗ trợ lưu trữ trong PostgreSQL
-   **Tương tác**: Giao tiếp với cơ sở dữ liệu PostgreSQL

### 6. Module Agent Creator (agent_creator.py)

-   **Mẫu thiết kế**: Factory Pattern
-   **Trách nhiệm**:
    -   Tạo các agent với cấu hình khác nhau
    -   Xác định luồng tư duy cho agent
-   **Tương tác**: Sử dụng LLM và tools để tạo agent

## Luồng Dữ Liệu Chính

1. **Luồng Xử Lý Câu Hỏi**:

```
Client → FastAPI → RAGAgent → (Tools + Vector DB) → LLM → Client
```

2. **Luồng Lưu Trữ Hội Thoại**:

```
RAGAgent → LLM → PostgreSQL → Lưu trữ/Truy xuất
```

3. **Luồng Xác Thực**:

```
Client → FastAPI → ID API → Xác thực → FastAPI → Xử lý yêu cầu
```

## Mẫu Thiết Kế Chính

### 1. Repository Pattern

Sử dụng trong `db_repository.py` và `chat_memory.py` để trừu tượng hóa và đóng gói logic truy cập dữ liệu, tách biệt khỏi logic nghiệp vụ.

### 2. Adapter Pattern

Được áp dụng trong `model.py` để cung cấp giao diện thống nhất cho các nhà cung cấp LLM khác nhau (OpenAI, Gemini, Palm).

### 3. Dependency Injection

FastAPI sử dụng DI để quản lý các dependency, ví dụ như việc xác thực token và khởi tạo RAG Agent.

### 4. Factory Pattern

Được sử dụng trong `agent_creator.py` để tạo các agent với cấu hình khác nhau mà không tiết lộ logic khởi tạo.

### 5. Command Pattern

Các công cụ trong `agent_tools.py` được thiết kế theo Command Pattern, cho phép encapsulate yêu cầu dưới dạng đối tượng.

## Nguyên Tắc SOLID

1. **Single Responsibility**: Mỗi module có một trách nhiệm rõ ràng (server.py xử lý API, model.py quản lý LLM, v.v.)

2. **Open/Closed**: Hệ thống có thể mở rộng thêm nhà cung cấp LLM hoặc công cụ mới mà không cần sửa đổi code hiện có.

3. **Liskov Substitution**: Các implementation của LLM từ các nhà cung cấp khác nhau có thể được sử dụng thay thế cho nhau.

4. **Interface Segregation**: API được thiết kế gọn nhẹ, mỗi endpoint phục vụ một mục đích cụ thể.

5. **Dependency Inversion**: Các module cấp cao (server) không phụ thuộc trực tiếp vào module cấp thấp, mà thông qua abstraction.

## Chiến Lược Mở Rộng

Hệ thống được thiết kế để dễ dàng mở rộng theo các hướng:

1. **Thêm Nhà Cung Cấp LLM Mới**:

    - Thêm adapter mới trong model.py
    - Không cần thay đổi code ở các module khác

2. **Thêm Công Cụ Mới**:

    - Định nghĩa công cụ mới trong agent_tools.py
    - Thêm vào danh sách công cụ

3. **Thêm Endpoint API**:
    - Định nghĩa endpoint mới trong server.py
    - Tận dụng lại các thành phần đã có
