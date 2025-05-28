import { useState, useEffect } from "react";
import { useChat } from "@/contexts/ChatContext";
import { useSettings } from "@/contexts/SettingsContext";
import Sidebar from "@/components/layout/Sidebar";
import Header from "@/components/layout/Header";
import Settings from "../ui/Settings";
import styles from "@/styles/Chat.module.css";
import { useAuth } from "@/hooks/useAuth";

interface LayoutProps {
    children: React.ReactNode;
}

const Layout = ({ children }: LayoutProps) => {
    const [settingsOpen, setSettingsOpen] = useState(false);
    const [sidebarVisible, setSidebarVisible] = useState(true);
    const [isMobile, setIsMobile] = useState(false);

    const {
        conversations,
        activeConversation,
        createNewChat,
        selectConversation,
        deleteConversation,
        clearCurrentChat,
    } = useChat();

    const { settings, updateSettings } = useSettings();
    const { logout } = useAuth();

    // Kiểm tra kích thước màn hình và thiết lập trạng thái mobile
    useEffect(() => {
        const checkMobile = () => {
            const mobile = window.innerWidth <= 768;

            // Chỉ cập nhật khi trạng thái thay đổi để tránh re-render không cần thiết
            if (mobile !== isMobile) {
                setIsMobile(mobile);

                // Tự động ẩn sidebar trên mobile khi lần đầu load
                if (mobile) {
                    setSidebarVisible(false);
                } else {
                    setSidebarVisible(true);
                }
            }
        };

        // Khởi tạo
        checkMobile();

        // Đăng ký sự kiện resize
        window.addEventListener("resize", checkMobile);

        return () => {
            window.removeEventListener("resize", checkMobile);
        };
    }, [isMobile]);

    const handleToggleSidebar = () => {
        console.log(`Toggle sidebar: ${sidebarVisible} -> ${!sidebarVisible}`);
        setSidebarVisible((prev) => !prev);
    };

    const handleOpenSettings = () => {
        setSettingsOpen(true);
    };

    const handleCloseSettings = () => {
        setSettingsOpen(false);
    };

    const handleNewChat = () => {
        createNewChat();
    };

    const handleLogout = () => {
        logout();
    };

    const handleExportChat = () => {
        console.log("Export chat");
    };

    const handleClearHistory = () => {
        console.log("Clear all history");
    };

    const handleUpdateSettings = (key: string, value: any) => {
        updateSettings(key as any, value);
    };

    // Tự động ẩn sidebar trên mobile khi chọn hội thoại
    const handleSelectChat = (id: string) => {
        selectConversation(id);
        if (isMobile) {
            setSidebarVisible(false);
        }
    };

    // Hàm xóa hội thoại
    const handleDeleteChat = (id: string) => {
        // Sử dụng hàm deleteConversation từ ChatContext
        deleteConversation(id);
    };

    // Hàm thay thế cho renameConversation đã bị loại bỏ
    const handleRenameChat = (id: string, newName: string) => {
        console.log("Chức năng đổi tên hội thoại đã bị vô hiệu hóa");
    };

    // Hàm xóa tin nhắn của cuộc trò chuyện hiện tại
    const handleClearChat = () => {
        // Sử dụng hàm clearCurrentChat từ ChatContext
        clearCurrentChat();
    };

    // Tính toán style cho main-content
    const mainContentStyle = {
        width: sidebarVisible && !isMobile ? "calc(100% - 280px)" : "100%",
        marginLeft: sidebarVisible && !isMobile ? "280px" : "0",
        transition: "all 0.3s ease",
    };

    return (
        <div className="app-container">
            {/* Sidebar */}
            <div
                className="sidebar-container"
                style={{
                    position: "fixed",
                    top: 0,
                    left: 0,
                    width: isMobile ? "85%" : "280px",
                    maxWidth: isMobile ? "300px" : "280px",
                    height: "100vh",
                    zIndex: 1020,
                    transform: sidebarVisible
                        ? "translateX(0)"
                        : "translateX(-100%)",
                    transition: "transform 0.3s ease",
                }}
            >
                <Sidebar
                    conversations={conversations}
                    activeConversation={activeConversation || ""}
                    onNewChat={handleNewChat}
                    onSelectChat={handleSelectChat}
                    onDeleteChat={handleDeleteChat}
                    onRenameChat={handleRenameChat}
                    isVisible={true}
                    onCloseSidebar={isMobile ? handleToggleSidebar : undefined}
                />
            </div>

            {/* Main content */}
            <div className={styles.mainContent} style={mainContentStyle}>
                <Header
                    toggleSidebar={handleToggleSidebar}
                    clearChat={handleClearChat}
                    openSettings={handleOpenSettings}
                    onLogout={handleLogout}
                    sidebarVisible={sidebarVisible}
                />

                {children}
            </div>

            {/* Overlay khi sidebar hiển thị trên mobile */}
            <div
                className={styles.overlay}
                onClick={handleToggleSidebar}
                style={{
                    display: isMobile && sidebarVisible ? "block" : "none",
                    zIndex: 999,
                    backgroundColor: "rgba(0, 0, 0, 0.3)",
                }}
            />

            {/* Settings panel */}
            <Settings
                isOpen={settingsOpen}
                closeSettings={handleCloseSettings}
                settings={settings}
                updateSettings={handleUpdateSettings}
                exportChat={handleExportChat}
                clearHistory={handleClearHistory}
            />
        </div>
    );
};

export default Layout;
