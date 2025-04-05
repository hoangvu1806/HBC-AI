# HBC AI Assistant API

API phục vụ cho ứng dụng HBC AI Assistant, hỗ trợ xác thực người dùng qua ID HBC.

## Cài đặt

1. Di chuyển vào thư mục API:

```bash
cd templates/api
```

2. Cài đặt các gói phụ thuộc:

```bash
npm install
```

## Chạy server

### Môi trường phát triển

```bash
npm run dev
```

### Môi trường sản xuất

```bash
npm start
```

Server sẽ chạy mặc định ở cổng 3000. Bạn có thể thay đổi cổng bằng cách thiết lập biến môi trường `PORT`.

## API Endpoints

### Kiểm tra Access Token

```
GET /api/check-access-token
```

#### Tham số

-   `accessToken`: Token truy cập cần kiểm tra
-   `hostUrl`: URL của host gọi API

#### Phản hồi

-   Nếu token hợp lệ:

```json
{
  "success": true,
  "user": {
    "id": "user_id",
    "name": "User Name",
    "email": "user@example.com",
    ...
  }
}
```

-   Nếu token không hợp lệ:

```json
{
    "success": false,
    "message": "Token không hợp lệ",
    "redirectUrl": "https://id-staging.hbc.com.vn?app_redirect_url=..."
}
```

## Lưu ý

Đây là API mock dùng cho môi trường phát triển. Trong môi trường sản xuất, bạn cần kết nối với API thật của ID HBC.
