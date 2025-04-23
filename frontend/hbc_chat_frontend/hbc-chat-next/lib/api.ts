// API endpoint base url
const API_URL = "https://aiapi.hbc.com.vn/api";

// ID HBC Login URL
export const ID_HBC_LOGIN_URL = "https://id-staging.hbc.com.vn";

// AES key cho việc giải mã dữ liệu từ ID HBC
export const GOOGLE_AES_KEY = "u2a0d40mf4b6t06s51oqkd20lqh132dq";

// Hàm xử lý cookie
export const getCookie = (name: string): string | null => {
    if (typeof window === "undefined") return null;

    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop()?.split(";").shift() || null;
    return null;
};

export const setCookie = (
    name: string,
    value: string,
    options: any = {}
): void => {
    if (typeof window === "undefined") return;

    let expires = options.expires
        ? `; expires=${options.expires.toUTCString()}`
        : "";
    let path = options.path ? `; path=${options.path}` : "";
    document.cookie = `${name}=${value}${expires}${path}`;
};

// Hàm kiểm tra access token
export const checkAccessToken = async (): Promise<any> => {
    try {
        let accessToken = getCookie("access_token");
        if (!accessToken) {
            throw new Error("Không tìm thấy access token");
        }
        const apiUrl = `https://id-api-staging.hbc.com.vn/v1/user/auth/google/access-token?accessToken=${encodeURIComponent(
            accessToken
        )}`;
        const response = await fetch(apiUrl, {
            method: "GET",
            headers: {
                "Content-Type": "application/json",
            },
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.message || "Không thể xác thực token");
        }

        return await response.json();
    } catch (error) {
        console.error("Lỗi kiểm tra token:", error);
        throw error;
    }
};

// Hàm làm mới access token
export const refreshAccessToken = async (): Promise<string> => {
    try {
        let refreshToken = getCookie("refresh_token");
        if (!refreshToken) {
            throw new Error("Không tìm thấy refresh token");
        }
        const response = await fetch(
            "https://id-api-staging.hbc.com.vn/v1/user/auth/google/access-token",
            {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    Authorization: "Bearer 1",
                },
                body: JSON.stringify({
                    refreshToken: refreshToken,
                    hostUrl: window.location.origin,
                }),
            }
        );

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.message || "Không thể làm mới token");
        }

        const data = await response.json();

        // Lưu token mới vào cookie
        setCookie("access_token", data.access_token, {
            path: "/",
            expires: new Date(Date.now() + data.expires_in * 1000),
        });
        if (data.refresh_token) {
            setCookie("refresh_token", data.refresh_token, {
                path: "/",
            });
        }
        return data.access_token;
    } catch (error) {
        console.error("Lỗi làm mới token:", error);
        throw error;
    }
};

// Hàm gọi API chat
export const callChatAPI = async (
    message: string,
    sessionName: string,
    topic: string = "HCNS",
    userEmail: string = "guest",
    thinkMode: boolean = false,
    files: File[] = []
): Promise<string> => {
    try {
        const apiUrl = `${API_URL}/chat`;
        const accessToken = getCookie("access_token");
        if (!accessToken) {
            throw new Error("Không tìm thấy access token");
        }

        // Chuẩn bị dữ liệu gửi đi
        const formData = new FormData();
        formData.append("topic", topic);
        formData.append("user_email", userEmail);
        formData.append("prompt", message);
        formData.append("session_name", sessionName);
        formData.append("mode", thinkMode ? "think" : "normal");

        // Thêm files nếu có
        if (files && files.length > 0) {
            files.forEach((file) => {
                formData.append("files", file);
            });
        }

        // Gửi yêu cầu đến API
        const response = await fetch(apiUrl, {
            method: "POST",
            headers: {
                Authorization: `Bearer ${accessToken}`,
            },
            body: formData,
        });

        // Kiểm tra trạng thái phản hồi
        if (!response.ok) {
            if (response.status === 401) {
                // Token không hợp lệ, thử làm mới
                try {
                    const newToken = await refreshAccessToken();
                    // Thử lại yêu cầu với token mới
                    const retryResponse = await fetch(apiUrl, {
                        method: "POST",
                        headers: {
                            Authorization: `Bearer ${newToken}`,
                        },
                        body: formData,
                    });
                    if (!retryResponse.ok) {
                        throw new Error(
                            `Retry failed: ${retryResponse.status} ${retryResponse.statusText}`
                        );
                    }
                    const retryData = await retryResponse.json();
                    return (
                        retryData.output || JSON.stringify(retryData, null, 2)
                    );
                } catch (refreshError) {
                    throw new Error("Không thể làm mới token");
                }
            } else {
                throw new Error(
                    `API error: ${response.status} ${response.statusText}`
                );
            }
        }

        // Xử lý dữ liệu từ phản hồi
        const data = await response.json();

        // Kiểm tra và trả về trường output nếu có
        if (data && data.output) {
            return data.output;
        } else if (data) {
            console.log("Phản hồi API không chứa trường output:", data);
            return JSON.stringify(data, null, 2);
        } else {
            return "Đã nhận được phản hồi từ API nhưng không có dữ liệu.";
        }
    } catch (error: any) {
        console.error("Lỗi khi gọi API:", error);
        throw error;
    }
};
