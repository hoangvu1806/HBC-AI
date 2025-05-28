import type { NextApiRequest, NextApiResponse } from "next";

type ResponseData = {
    success: boolean;
    message: string;
    data?: any;
    error?: any;
};

/**
 * API proxy để gửi dữ liệu feedback đến API server, giúp tránh vấn đề CORS
 */
export default async function handler(
    req: NextApiRequest,
    res: NextApiResponse<ResponseData>
) {
    // Chỉ chấp nhận phương thức POST
    if (req.method !== "POST") {
        return res.status(405).json({
            success: false,
            message: "Method Not Allowed",
        });
    }

    try {
        const { token, ...feedbackData } = req.body;

        if (!token) {
            return res.status(401).json({
                success: false,
                message: "Không tìm thấy token xác thực",
            });
        }

        console.log("Dữ liệu feedback nhận được:", feedbackData);

        // Sử dụng FormData thay vì JSON
        const formData = new URLSearchParams();
        for (const [key, value] of Object.entries(feedbackData)) {
            formData.append(key, String(value));
        }

        console.log("FormData được tạo:", formData.toString());

        // Gửi dữ liệu đến API thực tế
        const apiResponse = await fetch(
            "https://aiapi.hbc.com.vn/api/chat/feedback",
            {
                method: "POST",
                headers: {
                    "Content-Type": "application/x-www-form-urlencoded",
                    Authorization: `Bearer ${token}`,
                },
                body: formData,
            }
        );

        // Lấy dữ liệu phản hồi
        let responseData;
        const responseText = await apiResponse.text();
        console.log(`API Response Status: ${apiResponse.status}`);
        console.log(`API Response Text: ${responseText}`);

        try {
            // Thử parse dữ liệu JSON
            responseData = responseText ? JSON.parse(responseText) : null;
        } catch (e) {
            // Nếu không phải JSON, sử dụng text
            responseData = { text: responseText };
        }

        // Trả về kết quả cho client
        if (apiResponse.ok) {
            return res.status(200).json({
                success: true,
                message: "Gửi feedback thành công",
                data: responseData,
            });
        } else {
            return res.status(apiResponse.status).json({
                success: false,
                message: `Lỗi từ API: ${apiResponse.status} ${apiResponse.statusText}`,
                error: responseData,
            });
        }
    } catch (error: any) {
        console.error("Lỗi khi gửi feedback:", error);
        return res.status(500).json({
            success: false,
            message: "Lỗi server khi gửi feedback",
            error: error.message,
        });
    }
}
