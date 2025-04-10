# Dữ Liệu Hệ Thống Trợ Lý AI HBC

Thư mục này chứa dữ liệu tài liệu từ các phòng ban của Tập đoàn Xây dựng Hòa Bình (HBC) được sử dụng để huấn luyện và cung cấp thông tin cho hệ thống Trợ Lý AI.

## Cấu Trúc Thư Mục

```
data/
├── P.HCNS/               # Tài liệu phòng Hành chính nhân sự
├── HCNS_TXT/             # Tài liệu HCNS đã chuyển đổi sang text
├── HCNS_DATA_TEXT/       # Dữ liệu HCNS đã xử lý
├── P.CNTT/               # Tài liệu phòng Công nghệ thông tin
├── CNTT_DATA_TEXT/       # Dữ liệu CNTT đã xử lý
├── P.KDTT/               # Tài liệu phòng Kinh doanh thị trường
├── P.DVKH/               # Tài liệu phòng Dịch vụ khách hàng
├── P.MUA HANG/           # Tài liệu phòng Mua hàng
├── P.TCKT/               # Tài liệu phòng Tài chính kế toán
├── THONG BAO MOI/        # Thông báo mới (PDF)
├── THONG BAO MOI_TEXT/   # Thông báo mới (text)
└── cautruc/              # Thông tin về cấu trúc tài liệu
```

## Loại Dữ Liệu

### 1. Dữ Liệu Gốc (PDF)

Các thư mục chứa tài liệu gốc dạng PDF từ các phòng ban:

-   P.HCNS: Quy trình, quy định, biểu mẫu về nhân sự
-   P.CNTT: Hướng dẫn, quy trình về CNTT
-   P.KDTT: Tài liệu kinh doanh và thị trường
-   P.DVKH: Tài liệu dịch vụ khách hàng
-   P.MUA HANG: Quy trình, quy định về mua hàng
-   P.TCKT: Tài liệu tài chính kế toán
-   THONG BAO MOI: Các thông báo mới của công ty

### 2. Dữ Liệu Đã Xử Lý (Text)

Các thư mục chứa dữ liệu đã được chuyển đổi từ PDF sang text:

-   HCNS_TXT: Dữ liệu text từ tài liệu HCNS
-   CNTT_DATA_TEXT: Dữ liệu text từ tài liệu CNTT
-   HCNS_DATA_TEXT: Dữ liệu text từ tài liệu HCNS đã được tiền xử lý
-   THONG BAO MOI_TEXT: Thông báo mới dạng text

## Cấu Trúc Dữ Liệu

Mỗi tài liệu PDF thường có cấu trúc sau:

-   Mã số tài liệu
-   Ngày ban hành
-   Lần ban hành
-   Ngày hiệu lực
-   Nội dung chính
-   Phụ lục (nếu có)

## Quy Trình Xử Lý

1. Tài liệu PDF được lưu trữ trong thư mục tương ứng với phòng ban
2. Chuyển đổi PDF sang text bằng script `pdf_to_txt.py`
3. Tài liệu text được lưu trong thư mục `*_TXT` hoặc `*_DATA_TEXT`
4. Dữ liệu text được xử lý và nhúng vào cơ sở dữ liệu vector

## Lưu Ý

-   **KHÔNG** đưa các tài liệu nhạy cảm hoặc bí mật vào thư mục này
-   Tài liệu trong thư mục `TAI LIEU HET HIEU LUC DE THAM KHAO` chỉ dùng để tham khảo và không còn hiệu lực
-   Các thông báo mới sẽ được cập nhật thường xuyên trong thư mục `THONG BAO MOI`

## Bảo Mật

Dữ liệu trong thư mục này là thông tin nội bộ của Tập đoàn Xây dựng Hòa Bình và không được phép chia sẻ ra bên ngoài. Truy cập vào dữ liệu này phải tuân thủ các quy định về bảo mật thông tin của công ty.
