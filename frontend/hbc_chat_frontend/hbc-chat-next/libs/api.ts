// API Constants
const API_ENDPOINTS = {
    CHAT_API: "https://aiapi.hbc.com.vn/api/chat",
    CHECK_TOKEN: "https://aiapi.hbc.com.vn/v1/user/auth/google/access-token",
};

// Types
export interface ChatRequest {
    message: string;
    conversation_id?: string;
    think_mode?: boolean;
    files?: File[];
}

export interface ChatResponse {
    response: string;
    conversation_id: string;
}

export interface ApiError {
    message: string;
    status: number;
}

// Helper function to handle API errors
function handleApiError(error: any): ApiError {
    console.error("API Error:", error);
    if (error.response) {
        // The request was made and the server responded with a non-2xx status
        return {
            message: error.response.data.message || "Lỗi server",
            status: error.response.status,
        };
    } else if (error.request) {
        // The request was made but no response was received
        return {
            message: "Không thể kết nối đến server",
            status: 0,
        };
    } else {
        // Something else happened while setting up the request
        return {
            message: error.message || "Đã xảy ra lỗi",
            status: 0,
        };
    }
}

// Function to send chat message
export async function sendChatMessage(
    data: ChatRequest
): Promise<ChatResponse> {
    try {
        const formData = new FormData();
        formData.append("message", data.message);

        if (data.conversation_id) {
            formData.append("conversation_id", data.conversation_id);
        }

        if (data.think_mode !== undefined) {
            formData.append("think_mode", data.think_mode.toString());
        }

        if (data.files && data.files.length > 0) {
            data.files.forEach((file) => {
                formData.append("files", file);
            });
        }

        const response = await fetch(API_ENDPOINTS.CHAT_API, {
            method: "POST",
            body: formData,
            // Include credentials to send cookies with request
            credentials: "include",
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const result = await response.json();
        return result as ChatResponse;
    } catch (error) {
        throw handleApiError(error);
    }
}

// Function to validate token
export async function validateToken(): Promise<boolean> {
    try {
        const response = await fetch(API_ENDPOINTS.CHECK_TOKEN, {
            method: "GET",
            credentials: "include",
        });

        return response.ok;
    } catch (error) {
        console.error("Token validation error:", error);
        return false;
    }
}

export default {
    sendChatMessage,
    validateToken,
};
