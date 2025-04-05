# HBC AI Assistant

Ứng dụng chat bot trí tuệ nhân tạo phục vụ cho nhân viên HBC, tích hợp với hệ thống xác thực ID HBC.

## Cấu trúc dự án

```
templates/
  ├── index.html          # Trang web chính
  ├── script.js           # Logic JavaScript
  ├── styles.css          # Định dạng CSS
  ├── logo-HBC.png        # Logo công ty
  ├── settings.html       # Trang cài đặt
  ├── cors-guide.html     # Hướng dẫn CORS
  └── api/                # Backend API
       ├── server.js      # Server Express
       ├── check-access-token.js  # API kiểm tra token
       ├── package.json   # Quản lý phụ thuộc
       └── README.md      # Hướng dẫn API
```

## Tính năng

1. Xác thực người dùng thông qua ID HBC
2. Chat với AI Assistant
3. Hỗ trợ markdown cho văn bản phản hồi
4. Tải lên và gửi file
5. Đánh giá phản hồi
6. Lưu và khôi phục lịch sử trò chuyện
7. Chế độ tối/sáng
8. Quản lý đa phiên trò chuyện

## Cài đặt và chạy

### Frontend

Mở file `index.html` trong trình duyệt để sử dụng ứng dụng. Lưu ý rằng nếu bạn muốn tích hợp với API xác thực, bạn cần chạy backend.

### Backend API

Xem hướng dẫn trong thư mục `api/README.md`.

## Tích hợp với ID HBC

Ứng dụng được tích hợp với hệ thống xác thực của ID HBC. Người dùng sẽ được chuyển hướng đến trang đăng nhập ID HBC khi chưa đăng nhập. Sau khi đăng nhập thành công, người dùng sẽ được chuyển hướng trở lại ứng dụng với thông tin đăng nhập được lưu trữ an toàn trong cookie.

### Cấu hình

URL hệ thống ID HBC được cấu hình trong biến `ID_HBC_LOGIN_URL` trong file `script.js`:

```javascript
const ID_HBC_LOGIN_URL = "https://id-staging.hbc.com.vn";
```

## Bảo mật

-   Thông tin đăng nhập được lưu trong cookie với thời hạn tương ứng với token
-   Tất cả các yêu cầu API đều yêu cầu token xác thực
-   Không lưu trữ hoặc gửi mật khẩu người dùng
-   Dữ liệu trò chuyện được lưu trong localStorage của trình duyệt

## Phát triển

### Frontend

Dự án sử dụng JavaScript thuần không có framework. Để phát triển:

1. Chỉnh sửa files HTML, CSS và JavaScript
2. Làm mới trình duyệt để xem thay đổi

### Backend

Backend sử dụng Express.js. Để phát triển:

1. Cài đặt Node.js
2. Di chuyển đến thư mục api
3. Cài đặt dependencies với `npm install`
4. Chạy server với `npm run dev`

## Liên hệ

Để biết thêm thông tin hoặc báo cáo lỗi, vui lòng liên hệ qua email: [email@hbc.com.vn](mailto:email@hbc.com.vn)
