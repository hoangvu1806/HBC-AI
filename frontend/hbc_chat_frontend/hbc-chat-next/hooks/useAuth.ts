import { useState, useEffect } from "react";
import { checkAuth, logout, User, redirectToLogin } from "@/lib/auth";

interface AuthState {
    isLoading: boolean;
    isAuthenticated: boolean;
    user: User | null;
    login: () => void;
    logout: () => void;
}

/**
 * Hook để quản lý trạng thái xác thực của người dùng
 */
export function useAuth(): AuthState {
    const [isLoading, setIsLoading] = useState(true);
    const [isAuthenticated, setIsAuthenticated] = useState(false);
    const [user, setUser] = useState<User | null>(null);

    useEffect(() => {
        // Kiểm tra xác thực khi component mount
        const verifyAuth = async () => {
            setIsLoading(true);
            try {
                const userData = await checkAuth();

                if (userData) {
                    setUser(userData);
                    setIsAuthenticated(true);
                } else {
                    // Nếu không có người dùng, chuyển hướng đến trang đăng nhập
                    redirectToLogin();
                }
            } catch (error) {
                console.error("Lỗi xác thực:", error);
                // Nếu có lỗi, chuyển hướng đến trang đăng nhập
                redirectToLogin();
            } finally {
                setIsLoading(false);
            }
        };

        verifyAuth();
    }, []);

    const login = () => {
        redirectToLogin();
    };

    return {
        isLoading,
        isAuthenticated,
        user,
        login,
        logout,
    };
}
