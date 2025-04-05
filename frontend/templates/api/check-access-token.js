// API Endpoint kiểm tra access token
const express = require("express");
const router = express.Router();
const fetch = require("node-fetch");

// Lưu ý: Đây là mock API, trong thực tế cần thay thế bằng endpoint thật
const CHECK_ACCESS_TOKEN_URL =
    "https://id-api-staging.hbc.com.vn/v1/user/auth/google/access-token";

router.get("/check-access-token", async (req, res) => {
    try {
        const { accessToken, hostUrl } = req.query;

        if (!accessToken) {
            return res.status(401).json({
                success: false,
                message: "Token không được cung cấp",
                redirectUrl: `https://id-staging.hbc.com.vn?app_redirect_url=${Buffer.from(
                    hostUrl || ""
                ).toString("base64")}`,
            });
        }

        // Gọi API kiểm tra token
        const response = await fetch(CHECK_ACCESS_TOKEN_URL, {
            method: "GET",
            headers: {
                "Content-Type": "application/json",
                Authorization: `Bearer ${accessToken}`,
            },
            body: JSON.stringify({ hostUrl }),
        });

        const data = await response.json();

        // Nếu token hợp lệ
        if (response.ok) {
            return res.status(200).json({
                success: true,
                user: data.user,
            });
        }

        // Nếu token không hợp lệ
        return res.status(401).json({
            success: false,
            message: data.message || "Token không hợp lệ",
            redirectUrl: `https://id-staging.hbc.com.vn?app_redirect_url=${Buffer.from(
                hostUrl || ""
            ).toString("base64")}`,
        });
    } catch (error) {
        console.error("Lỗi kiểm tra access token:", error);
        return res.status(500).json({
            success: false,
            message: "Đã xảy ra lỗi khi kiểm tra token",
            redirectUrl: "https://id-staging.hbc.com.vn",
        });
    }
});

module.exports = router;
