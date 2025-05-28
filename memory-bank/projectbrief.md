# Dự Án Trợ Lý AI HBC - Project Brief

## Mục Tiêu

Phát triển một hệ thống trợ lý AI để hỗ trợ nhân viên Công ty Cổ phần Hòa Bình (HBC) truy xuất thông tin nội bộ, quy trình, chính sách và dữ liệu liên quan đến hoạt động của công ty một cách nhanh chóng, chính xác và hiệu quả.

## Phạm Vi Dự Án

-   Xây dựng backend API phục vụ tương tác với LLM (Large Language Model)
-   Tích hợp hệ thống RAG (Retrieval-Augmented Generation) để tìm kiếm thông tin từ cơ sở dữ liệu nội bộ
-   Phát triển khả năng truy vấn dữ liệu và cung cấp câu trả lời chính xác
-   Hỗ trợ nhiều nhà cung cấp LLM (OpenAI, Google Gemini, Palm)
-   Lưu trữ và quản lý lịch sử hội thoại
-   Cung cấp API cho các ứng dụng frontend kết nối

## Yêu Cầu Chính

1. **Chức Năng Trợ Lý AI**:

    - Trả lời câu hỏi dựa trên dữ liệu nội bộ
    - Cung cấp thông tin chính xác 100% dựa trên tài liệu có sẵn
    - Sử dụng RAG để truy xuất dữ liệu liên quan
    - Hỗ trợ nhiều ngữ cảnh trò chuyện

2. **Khả Năng Tích Hợp**:

    - API giao tiếp RESTful
    - Hỗ trợ streaming response
    - Tích hợp với cơ sở dữ liệu vector (Qdrant)
    - Hỗ trợ lưu trữ lịch sử trò chuyện (PostgreSQL)

3. **Tính Năng Quản Lý**:

    - Khởi tạo và quản lý phiên trò chuyện
    - Xóa lịch sử trò chuyện
    - Thay đổi nhà cung cấp LLM
    - Kiểm tra trạng thái hệ thống

4. **Bảo Mật**:
    - Xác thực người dùng thông qua token
    - Kiểm tra quyền truy cập API
    - Bảo vệ dữ liệu nhạy cảm

## Công Nghệ Sử Dụng

-   **Backend**: Python, FastAPI
-   **LLM**: OpenAI API, Google Gemini, Palm
-   **Vector Database**: Qdrant
-   **Memory Storage**: PostgreSQL
-   **Framework AI**: LangChain

## Đối Tượng Người Dùng

-   Nhân viên Công ty Cổ phần Hòa Bình
-   Đặc biệt tập trung vào nhân viên phòng Hành Chính Nhân Sự (HCNS)

## Kết Quả Mong Đợi

-   Hệ thống trợ lý AI đáp ứng câu hỏi với độ chính xác cao
-   Giảm thời gian tìm kiếm thông tin nội bộ cho nhân viên
-   Cung cấp trải nghiệm người dùng mượt mà thông qua API hiệu quả
-   Khả năng mở rộng và tích hợp với các ứng dụng khác trong tương lai
