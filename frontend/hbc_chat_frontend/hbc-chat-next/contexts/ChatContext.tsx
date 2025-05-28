import {
    createContext,
    useContext,
    useState,
    useEffect,
    ReactNode,
} from "react";
import { useSettings } from "@/contexts/SettingsContext";

// Khai báo kiểu dữ liệu cho CryptoJS
declare global {
    interface Window {
        CryptoJS: any;
    }
}

// Khai báo kiểu cho tin nhắn
export interface Message {
    id: string;
    content: string;
    isUser: boolean;
    timestamp: Date;
    role?: string;
    created_at?: string;
    hasFiles?: boolean;
}

// Khai báo kiểu cho hội thoại
export interface Conversation {
    id: string;
    name: string;
    messages: Message[];
    session_id?: string;
    expertor?: string;
    created_at?: string;
    updated_at?: string;
}

// Khai báo kiểu cho ngữ cảnh chat
interface ChatContextType {
    messages: Message[];
    conversations: Conversation[];
    activeConversation: string | null;
    isThinkModeActive: boolean;
    isWaitingResponse: boolean;
    sendMessage: (content: string) => void;
    createNewChat: () => void;
    selectConversation: (id: string | null) => void;
    toggleThinkMode: () => void;
    loadChatHistoryFromAPI: () => Promise<void>;
    deleteConversation: (id: string) => void;
    clearCurrentChat: () => void;
}

// Tạo Context
const ChatContext = createContext<ChatContextType | undefined>(undefined);

// Biến môi trường cho URL đăng nhập HBC
const ID_HBC_LOGIN_URL = "https://id-staging.hbc.com.vn";

// Khóa AES để giải mã dữ liệu từ ID HBC
const GOOGLE_AES_KEY = "u2a0d40mf4b6t06s51oqkd20lqh132dq";

// Provider component
export const ChatProvider = ({ children }: { children: ReactNode }) => {
    const [messages, setMessages] = useState<Message[]>([]);
    const [conversations, setConversations] = useState<Conversation[]>([]);
    const [activeConversation, setActiveConversation] = useState<string | null>(
        null
    );
    const [isThinkModeActive, setIsThinkModeActive] = useState(false);
    const [isWaitingResponse, setIsWaitingResponse] = useState(false);
    const [isAuthenticated, setIsAuthenticated] = useState(false);
    const [user, setUser] = useState<any>(null);
    const { settings } = useSettings();

    // Khởi tạo từ localStorage khi component được mount
    useEffect(() => {
        if (typeof window === "undefined") return;

        // Khôi phục chế độ think từ localStorage
        const thinkEnabled = localStorage.getItem("thinkEnabled");
        if (thinkEnabled !== null) {
            setIsThinkModeActive(thinkEnabled === "true");
        }

        // Kiểm tra xác thực
        checkAuth();
    }, []);

    // Lưu chế độ think khi thay đổi
    useEffect(() => {
        localStorage.setItem("thinkEnabled", isThinkModeActive.toString());
    }, [isThinkModeActive]);

    // Theo dõi thay đổi tin nhắn và cập nhật hội thoại hiện tại
    useEffect(() => {
        if (messages.length > 0 && activeConversation) {
            setConversations((prevConversations) => {
                return prevConversations.map((conv) => {
                    if (conv.id === activeConversation) {
                        return {
                            ...conv,
                            messages: messages,
                        };
                    }
                    return conv;
                });
            });
        }
    }, [messages, activeConversation]);

    // Tải lịch sử chat khi đã xác thực
    useEffect(() => {
        if (isAuthenticated) {
            loadChatHistoryFromAPI();
        }
    }, [isAuthenticated]);

    // Hàm kiểm tra cookie
    const getCookie = (name: string) => {
        const value = `; ${document.cookie}`;
        const parts = value.split(`; ${name}=`);
        if (parts.length === 2) return parts.pop()?.split(";").shift();
        return null;
    };

    // Hàm thiết lập cookie
    const setCookie = (name: string, value: string, options: any = {}) => {
        let expires = options.expires
            ? `; expires=${options.expires.toUTCString()}`
            : "";
        let path = options.path ? `; path=${options.path}` : "";
        document.cookie = `${name}=${value}${expires}${path}`;
    };

    // Hàm kiểm tra xác thực
    const checkAuth = async () => {
        try {
            // Kiểm tra token trong cookie
            let isToken =
                getCookie("access_token") || getCookie("refresh_token");

            // Kiểm tra dữ liệu callback trong URL
            const urlParams = new URLSearchParams(window.location.search);
            let isData = urlParams.get("data");

            if (isData) {
                await handleDataCallback(isData);
                // Xóa tham số data khỏi URL
                const newUrl = window.location.pathname + window.location.hash;
                window.history.replaceState({}, document.title, newUrl);
                return;
            }

            if (isToken) {
                try {
                    await checkAccessToken();
                    restoreUserInfo();
                    setIsAuthenticated(true);
                } catch (error) {
                    console.error("Lỗi kiểm tra token:", error);
                    redirectToLogin();
                }
            } else {
                redirectToLogin();
            }
        } catch (err) {
            console.error("Lỗi trong quá trình xác thực:", err);
            redirectToLogin();
        }
    };

    // Hàm chuyển hướng đến trang đăng nhập
    const redirectToLogin = () => {
        window.location.href = `${ID_HBC_LOGIN_URL}?app_redirect_url=${btoa(
            window.location.href
        )}`;
    };

    // Hàm kiểm tra access token
    const checkAccessToken = async () => {
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
                throw new Error(
                    errorData.message || "Không thể xác thực token"
                );
            }

            return await response.json();
        } catch (error) {
            console.error("Lỗi kiểm tra token:", error);
            throw error;
        }
    };

    // Hàm làm mới access token
    const refreshAccessToken = async () => {
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

    // Hàm xử lý dữ liệu callback từ ID HBC
    const handleDataCallback = async (data: string) => {
        if (typeof window === "undefined") return;

        try {
            if (typeof window.CryptoJS === "undefined") {
                await loadCryptoJS();
            }
            processDataCallback(data);
        } catch (error) {
            console.error("Lỗi xử lý callback:", error);
            redirectToLogin();
        }
    };

    // Hàm tải CryptoJS
    const loadCryptoJS = () => {
        return new Promise((resolve, reject) => {
            const script = document.createElement("script");
            script.src =
                "https://cdnjs.cloudflare.com/ajax/libs/crypto-js/4.1.1/crypto-js.min.js";
            script.integrity =
                "sha512-E8QSvWZ0eCLGk4km3hxSsNmGWbLtSCSUcewDQPQWZF6pEU8GlT8a5fF32wOl1i8ftdMhssTrF/OhyGWwonTcXA==";
            script.crossOrigin = "anonymous";
            script.referrerPolicy = "no-referrer";

            script.onload = () => resolve(true);
            script.onerror = (error) => reject(error);

            document.head.appendChild(script);
        });
    };

    // Hàm thực hiện xử lý dữ liệu callback
    const processDataCallback = (data: string) => {
        try {
            // Giải mã dữ liệu base64
            let dataDecodeBase64 = atob(data);

            if (typeof window.CryptoJS === "undefined") {
                throw new Error(
                    "CryptoJS chưa được tải. Vui lòng làm mới trang và thử lại."
                );
            }

            // Giải mã AES với khóa đã cung cấp
            const decryptedData = window.CryptoJS.AES.decrypt(
                dataDecodeBase64,
                GOOGLE_AES_KEY
            ).toString(window.CryptoJS.enc.Utf8);

            // Parse dữ liệu đăng nhập đã giải mã
            let dataLogin = JSON.parse(decryptedData);

            // Kiểm tra nếu user là false hoặc không tồn tại
            if (!dataLogin.user || dataLogin.user === false) {
                alert("Tài khoản chưa có quyền truy cập vào hệ thống.");
                redirectToLogin();
                return;
            }

            // Lưu thông tin người dùng vào localStorage
            localStorage.setItem("user", JSON.stringify(dataLogin.user));

            // Lưu token vào cookie
            setCookie("access_token", dataLogin.access_token, {
                path: "/",
                expires: new Date(Number(dataLogin.user.exp) * 1000),
            });
            setCookie("refresh_token", dataLogin.refresh_token, {
                path: "/",
            });

            // Cập nhật state người dùng
            setUser(dataLogin.user);
            setIsAuthenticated(true);
        } catch (err: any) {
            console.error("Lỗi xử lý dữ liệu callback:", err);
            alert(`Lỗi xử lý dữ liệu đăng nhập: ${err.message}`);
        }
    };

    // Khôi phục thông tin người dùng từ localStorage
    const restoreUserInfo = () => {
        try {
            const userData = localStorage.getItem("user");
            if (userData) {
                const user = JSON.parse(userData);
                setUser(user);
            }
        } catch (error) {
            console.error("Lỗi khi khôi phục thông tin người dùng:", error);
        }
    };

    // Tạo tên hội thoại không trùng
    const generateUniqueName = (baseName: string): string => {
        let nameCount = 1;
        let finalName = baseName;

        while (conversations.some((conv) => conv.name === finalName)) {
            finalName = `${baseName} (${nameCount})`;
            nameCount++;
        }

        return finalName;
    };

    // Khởi tạo hội thoại mới khi không có dữ liệu
    const resetConversations = () => {
        // Tạo hội thoại mới
        const newId = Date.now().toString();
        const newConversation: Conversation = {
            id: newId,
            name: generateUniqueName("Cuộc trò chuyện mới"),
            messages: [],
        };

        // Cập nhật state
        setConversations([newConversation]);
        setActiveConversation(newId);
        setMessages([]);
    };

    // Tạo một cuộc trò chuyện mới
    const createNewChat = (): string => {
        // Tạo ID và tên mới
        const newId = Date.now().toString();
        const finalName = generateUniqueName("Cuộc trò chuyện mới");

        const newConversation: Conversation = {
            id: newId,
            name: finalName,
            messages: [],
        };

        // Thêm hội thoại mới vào danh sách
        setConversations((prevConversations) => [
            newConversation,
            ...prevConversations,
        ]);

        // Chuyển đến hội thoại mới
        setActiveConversation(newId);
        setMessages([]);

        return newId;
    };

    // Chọn một cuộc trò chuyện
    const selectConversation = (id: string | null) => {
        if (!id) return;

        const conversation = conversations.find((conv) => conv.id === id);
        if (!conversation) return;

        setActiveConversation(id);
        setMessages(conversation.messages);
    };

    // Bật/tắt chế độ Think
    const toggleThinkMode = () => {
        // Nếu là NGHI_PHEP, luôn tắt chế độ think
        if (settings.aiTopic === "NGHI_PHEP") {
            setIsThinkModeActive(false);
            return;
        }
        setIsThinkModeActive(!isThinkModeActive);
    };

    // Hàm khác để đảm bảo isThinkModeActive luôn false khi aiTopic là NGHI_PHEP
    useEffect(() => {
        if (settings.aiTopic === "NGHI_PHEP" && isThinkModeActive) {
            setIsThinkModeActive(false);
        }
    }, [settings.aiTopic]);

    // Gửi tin nhắn
    const sendMessage = async (content: string) => {
        if (!content.trim()) return;

        // Đánh dấu đang đợi phản hồi
        setIsWaitingResponse(true);

        // Lấy hoặc tạo ID hội thoại
        let currentConversationId = activeConversation;
        if (!currentConversationId) {
            currentConversationId = createNewChat();
        }

        // Tạo tin nhắn người dùng
        const userMessage: Message = {
            id: `msg-${Date.now()}-${Math.floor(Math.random() * 1000)}`,
            content: content,
            isUser: true,
            timestamp: new Date(),
        };

        // Cập nhật tin nhắn hiện tại
        setMessages((prevMessages) => [...prevMessages, userMessage]);

        // Cập nhật tin nhắn trong conversations
        setConversations((prevConversations) =>
            prevConversations.map((conv) =>
                conv.id === currentConversationId
                    ? { ...conv, messages: [...conv.messages, userMessage] }
                    : conv
            )
        );

        // Gọi API để lấy phản hồi
        try {
            const botResponse = await callChatAPI(content);

            if (botResponse === null) {
                setIsWaitingResponse(false);
                return;
            }

            // Tạo tin nhắn bot
            const botMessage: Message = {
                id: `msg-${Date.now()}-${Math.floor(Math.random() * 1000)}`,
                content: botResponse,
                isUser: false,
                timestamp: new Date(),
            };

            // Cập nhật tin nhắn
            setMessages((prevMessages) => [...prevMessages, botMessage]);
            setConversations((prevConversations) =>
                prevConversations.map((conv) =>
                    conv.id === currentConversationId
                        ? { ...conv, messages: [...conv.messages, botMessage] }
                        : conv
                )
            );
        } catch (error: any) {
            // Tạo tin nhắn lỗi
            const errorMessage: Message = {
                id: `msg-${Date.now()}-${Math.floor(Math.random() * 1000)}`,
                content: `Đã xảy ra lỗi: ${error.message}. Vui lòng thử lại sau.`,
                isUser: false,
                timestamp: new Date(),
            };

            // Cập nhật tin nhắn
            setMessages((prevMessages) => [...prevMessages, errorMessage]);
            setConversations((prevConversations) =>
                prevConversations.map((conv) =>
                    conv.id === currentConversationId
                        ? {
                              ...conv,
                              messages: [...conv.messages, errorMessage],
                          }
                        : conv
                )
            );
        } finally {
            // Đặt lại trạng thái đợi phản hồi
            setIsWaitingResponse(false);
        }
    };

    // Hàm gọi API chat
    const callChatAPI = async (message: string) => {
        try {
            const apiUrl = "https://aiapi.hbc.com.vn/api/chat";
            const accessToken = getCookie("access_token");
            const refreshToken = getCookie("refresh_token");
            if (!accessToken) {
                throw new Error("Không tìm thấy access token");
            }

            // Lấy tên hội thoại
            const currentConv = conversations.find(
                (conv) => conv.id === activeConversation
            );
            const sessionName = currentConv
                ? currentConv.name
                : "Cuộc trò chuyện mới";

            // Lấy thông tin người dùng
            let userEmail = "guest";
            let userName = "guest";
            if (user) {
                console.log(user);
                userEmail = user.emailAddress || "guest";
                userName = user.displayName || "guest";
            }

            // Chuẩn bị dữ liệu
            const formData = new FormData();
            formData.append("topic", settings.aiTopic);
            formData.append("user_email", userEmail);
            formData.append("user_name", userName);
            formData.append("prompt", message);
            formData.append("session_name", sessionName);
            formData.append("refresh_token", refreshToken || "");
            formData.append("mode", isThinkModeActive ? "think" : "normal");

            // Gửi yêu cầu
            const response = await fetch(apiUrl, {
                method: "POST",
                headers: {
                    Authorization: `Bearer ${accessToken}`,
                },
                body: formData,
            });

            // Xử lý lỗi 401
            if (!response.ok) {
                if (response.status === 401) {
                    try {
                        const newToken = await refreshAccessToken();
                        const retryResponse = await fetch(apiUrl, {
                            method: "POST",
                            headers: {
                                Authorization: `Bearer ${newToken}`,
                            },
                            body: formData,
                        });

                        if (!retryResponse.ok) {
                            throw new Error(
                                `Retry failed: ${retryResponse.status}`
                            );
                        }

                        const retryData = await retryResponse.json();
                        return (
                            retryData.output ||
                            JSON.stringify(retryData, null, 2)
                        );
                    } catch (refreshError) {
                        alert("Vui lòng đăng nhập lại");
                        redirectToLogin();
                        return null;
                    }
                } else {
                    throw new Error(`API error: ${response.status}`);
                }
            }

            // Xử lý dữ liệu
            const data = await response.json();
            return data.output || JSON.stringify(data, null, 2);
        } catch (error: any) {
            console.error("Lỗi khi gọi API:", error);
            if (error.message === "Không thể làm mới token") {
                redirectToLogin();
                return null;
            }
            return `Hiện đang có lỗi phía server: ${error.message}. Vui lòng thử lại sau.`;
        }
    };

    // Hàm tải lịch sử chat từ API
    const loadChatHistoryFromAPI = async () => {
        try {
            // Lấy email người dùng
            let userEmail = "guest";
            if (user && user.emailAddress) {
                userEmail = user.emailAddress;
            } else {
                const userData = localStorage.getItem("user");
                if (userData) {
                    const parsedUser = JSON.parse(userData);
                    userEmail = parsedUser.emailAddress || "guest";
                }
            }

            const accessToken = getCookie("access_token");
            if (!accessToken) {
                resetConversations();
                return;
            }

            // Gọi API
            const response = await fetch(
                `https://aiapi.hbc.com.vn/api/chat/sessions?user_email=${encodeURIComponent(
                    userEmail
                )}`,
                {
                    method: "GET",
                    headers: {
                        Authorization: `Bearer ${accessToken}`,
                        "Content-Type": "application/json",
                    },
                }
            );

            // Xử lý lỗi 401
            if (!response.ok) {
                if (response.status === 401) {
                    try {
                        const newToken = await refreshAccessToken();
                        const retryResponse = await fetch(
                            `https://aiapi.hbc.com.vn/api/chat/sessions?user_email=${encodeURIComponent(
                                userEmail
                            )}`,
                            {
                                method: "GET",
                                headers: {
                                    Authorization: `Bearer ${newToken}`,
                                    "Content-Type": "application/json",
                                },
                            }
                        );

                        if (!retryResponse.ok) {
                            throw new Error(
                                `Retry failed: ${retryResponse.status}`
                            );
                        }

                        const data = await retryResponse.json();
                        processSessionData(data);
                    } catch (refreshError) {
                        alert("Vui lòng đăng nhập lại");
                        redirectToLogin();
                        return;
                    }
                } else {
                    resetConversations();
                    return;
                }
            } else {
                const data = await response.json();
                processSessionData(data);
            }
        } catch (error) {
            console.error("Lỗi khi lấy lịch sử chat từ API:", error);
            resetConversations();
        }
    };

    // Hàm xử lý dữ liệu session từ API
    const processSessionData = (data: any) => {
        if (data.status !== "success" || !Array.isArray(data.sessions)) {
            resetConversations();
            return;
        }

        // Chuyển đổi dữ liệu từ API sang định dạng Conversation
        const apiConversations: Conversation[] = data.sessions.map(
            (session: any) => {
                // Chuyển đổi tin nhắn
                const convertedMessages: Message[] = session.messages.map(
                    (msg: any) => {
                        let timestamp = new Date(msg.created_at);
                        if (isNaN(timestamp.getTime())) {
                            timestamp = new Date();
                        }

                        return {
                            id: `msg-${Date.now()}-${Math.floor(
                                Math.random() * 1000
                            )}`,
                            content: msg.content,
                            isUser: msg.role === "user",
                            timestamp: timestamp,
                            role: msg.role,
                            created_at: msg.created_at,
                        };
                    }
                );

                return {
                    id: session.session_id,
                    name: session.session_name,
                    messages: convertedMessages,
                    session_id: session.session_id,
                    expertor: session.expertor,
                    created_at: session.created_at,
                    updated_at: session.updated_at,
                };
            }
        );

        // Cập nhật state
        if (apiConversations.length > 0) {
            setConversations(apiConversations);
            setActiveConversation(apiConversations[0].id);
            setMessages(apiConversations[0].messages);
        } else {
            resetConversations();
        }
    };

    // Xóa một cuộc trò chuyện
    const deleteConversation = (id: string) => {
        // Xóa cuộc trò chuyện khỏi danh sách
        const updatedConversations = conversations.filter(
            (conv) => conv.id !== id
        );

        // Cập nhật trạng thái
        setConversations(updatedConversations);

        // Nếu xóa cuộc trò chuyện hiện tại, chuyển sang cuộc trò chuyện khác
        if (id === activeConversation) {
            if (updatedConversations.length > 0) {
                setActiveConversation(updatedConversations[0].id);
                setMessages(updatedConversations[0].messages);
            } else {
                // Nếu không còn cuộc trò chuyện nào, tạo mới
                createNewChat();
            }
        }
    };

    // Xóa tin nhắn của cuộc trò chuyện hiện tại
    const clearCurrentChat = () => {
        if (!activeConversation) {
            return;
        }

        // Cập nhật trạng thái
        setMessages([]);
        setConversations((prevConversations) =>
            prevConversations.map((conv) => {
                if (conv.id === activeConversation) {
                    return {
                        ...conv,
                        messages: [],
                    };
                }
                return conv;
            })
        );
    };

    return (
        <ChatContext.Provider
            value={{
                messages,
                conversations,
                activeConversation,
                isThinkModeActive,
                isWaitingResponse,
                sendMessage,
                createNewChat,
                selectConversation,
                toggleThinkMode,
                loadChatHistoryFromAPI,
                deleteConversation,
                clearCurrentChat,
            }}
        >
            {children}
        </ChatContext.Provider>
    );
};

// Hook để sử dụng context
export const useChat = () => {
    const context = useContext(ChatContext);
    if (context === undefined) {
        throw new Error("useChat must be used within a ChatProvider");
    }
    return context;
};
