# Ngữ Cảnh Hiện Tại - Trợ Lý AI HBC

## Trạng Thái Dự Án

Dự án Trợ Lý AI HBC hiện đang ở giai đoạn hoạt động và được triển khai trong môi trường nội bộ của công ty. Hệ thống đang phục vụ chủ yếu cho nhân viên phòng Hành Chính Nhân Sự (HCNS) và đang dần mở rộng cho các phòng ban khác.

## Tính Năng Hoạt Động

Hệ thống hiện đã triển khai các tính năng chính:

1. **API Chat với RAG**:

    - Truy vấn thông tin từ cơ sở dữ liệu Qdrant
    - Tích hợp với mô hình ngôn ngữ (OpenAI,...)
    - Hỗ trợ trả lời cả dạng đồng bộ và streaming

2. **Quản Lý Phiên**:

    - Khởi tạo và lưu trữ phiên chat
    - Truy xuất lịch sử hội thoại
    - Xóa phiên chat khi cần thiết

3. **Công Cụ (Tools)**:

    - Tìm kiếm tài liệu (search_documents)
    - Tìm kiếm FAQ (search_qa)
    - Tra cứu thông tin liên hệ (get_contact_info)
    - Lấy thời gian hiện tại (get_current_datetime)
    - Truy vấn thông tin công ty (get_company_info)
    - Tìm kiếm web (web_search) khi cần

4. **Xác Thực và Phân Quyền**:
    - Tích hợp với ID API của HBC
    - Xác thực qua token

## Kết Nối và Tích Hợp

Hệ thống đang được sử dụng và kết nối với:

1. **Frontend Web Application**:

    - Giao diện chat thân thiện
    - Tích hợp với hệ thống phân quyền HBC

2. **Cơ Sở Dữ Liệu Tài Liệu**:

    - Collection HBC_P_HCNS_KNOWLEDGE_BASE trong Qdrant
    - Chứa thông tin về chính sách, quy trình, quy định của công ty

3. **PostgreSQL**:
    - Lưu trữ lịch sử hội thoại
    - Quản lý session và phân tích dữ liệu

## Quyết Định Hiện Tại

1. **Sử Dụng Đa Nhà Cung Cấp LLM**:

    - OpenAI là nhà cung cấp mặc định (gpt-4.1-mini)

2. **Kiến Trúc RAG với Qdrant**:

    - Sử dụng Retrieval-Augmented Generation để trả lời chính xác
    - Embedding được tạo với OpenAI text-embedding-3-small
    - Tìm kiếm similarity trong Qdrant

3. **System Prompt Tùy Chỉnh**:

    - Tập trung vào vai trò trợ lý nội bộ HBC
    - Ưu tiên thông tin chính xác từ tài liệu nội bộ
    - Từ chối trả lời câu hỏi ngoài phạm vi công ty

4. **Lưu Trữ PostgreSQL cho Memory**:
    - Duy trì lịch sử trò chuyện qua các phiên
    - Cho phép phân tích và cải thiện hệ thống
    - Bảo mật thông tin người dùng

## Thách Thức Hiện Tại

1. **Cải Thiện Độ Chính Xác**:

    - Tiếp tục tinh chỉnh RAG để trả lời chính xác hơn
    - Xử lý tốt hơn các câu hỏi mơ hồ hoặc thiếu thông tin

2. **Tối Ưu Hiệu Năng**:

    - Giảm độ trễ khi xử lý câu hỏi phức tạp
    - Cải thiện tốc độ truy xuất từ Qdrant

3. **Mở Rộng Phạm Vi Dữ Liệu**:

    - Thêm tài liệu từ các phòng ban khác
    - Cập nhật thường xuyên dữ liệu trong vector database

4. **Phản Hồi Người Dùng**:
    - Thu thập và phân tích phản hồi để cải thiện
    - Giải quyết các trường hợp không trả lời được hoặc không chính xác

## Kế Hoạch Ngắn Hạn

1. **Tăng Cường Dữ Liệu**:

    - Cập nhật tài liệu HCNS mới nhất vào vector database
    - Mở rộng phạm vi với tài liệu từ phòng Tài chính và Kinh doanh

2. **Cải Thiện UI/UX**:

    - Tối ưu hóa trải nghiệm streaming response
    - Thêm tính năng đề xuất câu hỏi thường gặp

3. **Xây Dựng Báo Cáo Phân Tích**:

    - Tạo dashboard theo dõi việc sử dụng hệ thống
    - Phân tích xu hướng câu hỏi để cải thiện tài liệu

4. **Tìm Hiểu Mô Hình LLM Mới**:
    - Đánh giá hiệu suất của gpt-4o-mini so với các mô hình mới
    - Cân nhắc triển khai mô hình mã nguồn mở local nếu phù hợp

## Điểm Cần Lưu Ý

1. **Xử Lý Token Rate Limit**:

    - Cần giám sát và xử lý khi đạt giới hạn token từ OpenAI
    - Có cơ chế fallback sang nhà cung cấp khác khi cần

2. **Đảm Bảo Tính Riêng Tư**:

    - Tuân thủ quy định nội bộ về bảo mật thông tin
    - Không lưu trữ thông tin nhạy cảm trong lịch sử chat

3. **Cập Nhật System Prompt**:

    - Điều chỉnh system prompt khi có yêu cầu mới
    - Đảm bảo AI luôn tuân thủ quy tắc phản hồi của công ty

4. **Theo Dõi Hiệu Suất Server**:
    - Giám sát tài nguyên của FastAPI server
    - Chuẩn bị phương án scale khi cần thiết
