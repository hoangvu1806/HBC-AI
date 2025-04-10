# Hệ Thống Nhúng Dữ Liệu (Embedding)

Thành phần này của hệ thống Trợ Lý AI HBC chịu trách nhiệm xử lý, nhúng và lưu trữ dữ liệu vào cơ sở dữ liệu vector để phục vụ cho RAG (Retrieval-Augmented Generation).

## Quy Trình Xử Lý Dữ Liệu

Quy trình tổng quan của việc xử lý và nhúng dữ liệu bao gồm các bước sau:

1. **Thu thập dữ liệu**: Tài liệu PDF từ các phòng ban
2. **Tiền xử lý**: Chuyển đổi PDF sang văn bản
3. **Phân đoạn**: Chia nhỏ văn bản thành các phần có độ dài phù hợp
4. **Trích xuất metadata**: Lấy thông tin quan trọng từ văn bản
5. **Tạo embedding**: Tạo vector biểu diễn cho mỗi phần văn bản
6. **Lưu trữ**: Lưu văn bản và vector vào cơ sở dữ liệu Qdrant

## Các File Chính

-   **embedding.py**: Script chính để tạo và lưu trữ embedding từ văn bản
-   **extractor.py**: Trích xuất metadata từ tài liệu
-   **pdf_to_txt.py**: Chuyển đổi tệp PDF sang định dạng văn bản

## Cách Sử Dụng

### Chuyển Đổi PDF sang Text

```bash
python pdf_to_txt.py --input_dir data/P.HCNS --output_dir data/HCNS_TXT
```

Tham số:

-   `--input_dir`: Thư mục chứa tệp PDF
-   `--output_dir`: Thư mục đầu ra cho tệp văn bản

### Tạo và Lưu Trữ Embedding

```bash
python embedding.py
```

Lưu ý: Đảm bảo đã cấu hình các biến môi trường cần thiết trong file `.env`:

```
OPENAI_API_KEY=your_openai_api_key
```

## Cấu Trúc Dữ Liệu

Mỗi đoạn văn bản được nhúng sẽ có cấu trúc sau trong cơ sở dữ liệu Qdrant:

```json
{
  "id": "<id>",
  "vector": [...],
  "payload": {
    "content": "<nội dung văn bản>",
    "metadata": {
      "file_name": "<tên file>",
      "section": "<phần>",
      "department": "<phòng ban>",
      "group": "<nhóm>",
      "company": "HBC",
      "year": "<năm>",
      "access_level": "internal",
      "issue_number": "<số phát hành>",
      "effective_date": "<ngày hiệu lực>",
      "revision": "<số lần sửa đổi>",
      "issue_date": "<ngày phát hành>",
      "file_path": "<đường dẫn file>"
    }
  }
}
```

## Mô Hình Nhúng

Hệ thống sử dụng mô hình `text-embedding-3-large` của OpenAI để tạo embedding với kích thước vector 3072 chiều.

## Tối Ưu Hóa

-   **Kích thước đoạn**: Đoạn văn bản được cấu hình với kích thước mặc định 1200 ký tự và độ chồng lấp 300 ký tự
-   **Xử lý hàng loạt**: Để tăng hiệu suất, hệ thống xử lý và tải dữ liệu theo batch (mặc định 3 văn bản/batch)
-   **Tìm điểm ngắt tự nhiên**: Thuật toán tìm vị trí kết thúc câu gần nhất để chia văn bản một cách hợp lý

## Xử Lý Lỗi

Hệ thống có xử lý các lỗi phổ biến:

-   Lỗi khi đọc file
-   Lỗi khi tạo embedding
-   Lỗi khi upload batch vào Qdrant

## Các Bộ Dữ Liệu

Hệ thống đã được thiết kế để xử lý dữ liệu từ các phòng ban:

-   P.HCNS: Tài liệu nhân sự
-   P.CNTT: Tài liệu CNTT
-   P.KDTT: Tài liệu kinh doanh
-   P.DVKH: Tài liệu dịch vụ khách hàng
-   P.MUA HANG: Tài liệu mua hàng
-   P.TCKT: Tài liệu tài chính kế toán
