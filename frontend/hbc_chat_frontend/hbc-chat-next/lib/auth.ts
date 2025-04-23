import { getCookie, setCookie, ID_HBC_LOGIN_URL, GOOGLE_AES_KEY } from "./api";

export interface User {
    id?: string;
    displayName?: string;
    emailAddress?: string;
    picture?: string;
    exp?: number;
    [key: string]: any;
}

// Chuyển hướng đến trang đăng nhập ID HBC
export const redirectToLogin = () => {
    if (typeof window !== "undefined") {
        window.location.href = `${ID_HBC_LOGIN_URL}?app_redirect_url=${btoa(
            window.location.href
        )}`;
    }
};

// Hàm tải CryptoJS khi cần
export const loadCryptoJS = (): Promise<boolean> => {
    return new Promise((resolve, reject) => {
        if (typeof window === "undefined") {
            reject(new Error("Window is not defined"));
            return;
        }

        // Kiểm tra nếu CryptoJS đã được tải
        if (typeof (window as any).CryptoJS !== "undefined") {
            resolve(true);
            return;
        }

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

// Giải mã dữ liệu callback từ ID HBC
export const processDataCallback = (data: string): User => {
    if (typeof window === "undefined") {
        throw new Error("Window is not defined");
    }

    try {
        // Giải mã dữ liệu base64
        let dataDecodeBase64 = atob(data);

        if (typeof (window as any).CryptoJS === "undefined") {
            throw new Error(
                "CryptoJS chưa được tải. Vui lòng làm mới trang và thử lại."
            );
        }

        // Giải mã AES với khóa đã cung cấp
        const CryptoJS = (window as any).CryptoJS;
        const decryptedData = CryptoJS.AES.decrypt(
            dataDecodeBase64,
            GOOGLE_AES_KEY
        ).toString(CryptoJS.enc.Utf8);

        // Parse dữ liệu đăng nhập đã giải mã
        let dataLogin = JSON.parse(decryptedData);

        // Kiểm tra nếu user là false hoặc không tồn tại
        if (!dataLogin.user || dataLogin.user === false) {
            throw new Error("Tài khoản chưa có quyền truy cập vào hệ thống.");
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

        return dataLogin.user;
    } catch (err: any) {
        console.error("Lỗi xử lý dữ liệu callback:", err);
        throw new Error(`Lỗi xử lý dữ liệu đăng nhập: ${err.message}`);
    }
};

// Hàm kiểm tra và xử lý xác thực
export const checkAuth = async (): Promise<User | null> => {
    if (typeof window === "undefined") return null;

    try {
        // Kiểm tra xem có access_token hoặc refresh_token trong cookie không
        let isToken = getCookie("access_token") || getCookie("refresh_token");

        // Kiểm tra xem có dữ liệu callback từ ID HBC trong URL không
        const urlParams = new URLSearchParams(window.location.search);
        let isData = urlParams.get("data");

        if (isData) {
            // Tải CryptoJS nếu cần
            if (typeof (window as any).CryptoJS === "undefined") {
                await loadCryptoJS();
            }

            // Xử lý dữ liệu callback
            const user = processDataCallback(isData);

            // Xóa tham số data khỏi URL
            const newUrl = window.location.pathname + window.location.hash;
            window.history.replaceState({}, document.title, newUrl);

            return user;
        }

        if (isToken) {
            // Khôi phục thông tin người dùng từ localStorage
            const userData = localStorage.getItem("user");
            if (userData) {
                return JSON.parse(userData);
            }
            return null;
        } else {
            // Không có token, cần đăng nhập
            return null;
        }
    } catch (err) {
        console.error("Lỗi trong quá trình xác thực:", err);
        return null;
    }
};

// Hàm đăng xuất
export const logout = () => {
    if (typeof window === "undefined") return;

    // Xóa cookies và localStorage
    document.cookie =
        "access_token=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";
    document.cookie =
        "refresh_token=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";
    localStorage.removeItem("user");

    // Chuyển hướng đến trang đăng nhập
    redirectToLogin();
};
