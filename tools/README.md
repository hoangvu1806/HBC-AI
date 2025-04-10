# Công Cụ và Tiện Ích

Thư mục này chứa các công cụ và tiện ích bổ sung hỗ trợ cho hệ thống Trợ Lý AI HBC. Các công cụ này cung cấp chức năng mở rộng và tương tác với hệ thống chính.

## Các Thành Phần Chính

### Tools Server

File `tools_server.py` triển khai một máy chủ công cụ cung cấp các chức năng bổ sung cho mô hình ngôn ngữ lớn (LLM), cho phép LLM truy cập dữ liệu thời gian thực và thực hiện các hành động.

## Cách Sử Dụng

### Khởi Động Tools Server

```bash
./run_tools_server.sh
```

Hoặc chạy trực tiếp:

```bash
python tools/tools_server.py
```

Mặc định, tools server sẽ chạy trên cổng 8082.

## API Endpoints

Máy chủ công cụ cung cấp một số API endpoints cho phép LLM:

-   Truy vấn dữ liệu thời gian thực
-   Tìm kiếm thông tin bổ sung
-   Thực hiện các hành động theo yêu cầu của người dùng

## Cấu Hình

Bạn có thể điều chỉnh cấu hình của tools server bằng cách chỉnh sửa các biến trong file `tools_server.py`.

## Bảo Mật

Tools server cung cấp quyền truy cập vào các chức năng bổ sung cho LLM. Hãy đảm bảo cấu hình bảo mật thích hợp để ngăn chặn truy cập trái phép và giới hạn phạm vi hoạt động của các công cụ.

## Mở Rộng

Để thêm công cụ mới:

1. Định nghĩa hàm công cụ mới trong file `tools_server.py`
2. Đăng ký công cụ trong danh sách công cụ
3. Cung cấp tài liệu và mô tả chi tiết cho công cụ

## Yêu Cầu

-   Python 3.8+
-   FastAPI
-   Uvicorn
-   Các thư viện phụ thuộc khác được liệt kê trong requirements.txt

## Liên Hệ

Nếu bạn có câu hỏi hoặc gặp vấn đề với các công cụ, vui lòng liên hệ phòng CNTT - Công ty Cổ phần Tập đoàn Xây dựng Hòa Bình.
