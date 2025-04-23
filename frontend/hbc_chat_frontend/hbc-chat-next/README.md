# HBC Chat - NextJS

Dự án chat bot HBC được viết lại sử dụng NextJS.

## Công nghệ sử dụng

-   NextJS 14
-   React 18
-   TypeScript
-   Zustand (state management)
-   Marked (Markdown renderer)
-   Highlight.js (Code syntax highlighting)

## Tính năng

-   Giao diện giống ChatGPT
-   Hỗ trợ Markdown trong tin nhắn
-   Quản lý đa hội thoại
-   Dark mode
-   Đánh giá tin nhắn
-   Tải lên file
-   Chế độ "Think" (suy nghĩ)
-   Responsive (điện thoại, tablet, desktop)

## Cài đặt

```bash
# Cài đặt dependencies
npm install

# Khởi chạy môi trường development
npm run dev

# Build cho production
npm run build

# Chạy phiên bản production
npm start
```

## Cấu trúc thư mục

```
hbc-chat-next/
├── components/     # React components
│   ├── chat/       # Components liên quan đến chat
│   ├── layout/     # Components liên quan đến layout
│   └── ui/         # UI components tái sử dụng
├── contexts/       # React contexts
├── hooks/          # Custom hooks
├── libs/           # Thư viện và utilities
├── pages/          # Next.js pages
├── public/         # Static assets
└── styles/         # CSS modules và globals
```

## API Endpoints

-   `https://aiapi.hbc.com.vn/api/chat` - API chat
-   `https://aiapi.hbc.com.vn/v1/user/auth/google/access-token` - API xác thực
