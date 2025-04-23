import { useState, useEffect, useRef, useCallback } from "react";
import {
    FaCog,
    FaTrash,
    FaSignOutAlt,
    FaBars,
    FaMoon,
    FaSun,
    FaAngleRight,
    FaEraser,
    FaAngleLeft,
} from "react-icons/fa";
import styles from "@/styles/Chat.module.css";
import { useChat } from "@/contexts/ChatContext";
import { useAuth } from "@/hooks/useAuth";
import { useSettings } from "@/contexts/SettingsContext";
import Image from "next/image";
import ConfirmDialog from "../ui/ConfirmDialog";

interface HeaderProps {
    toggleSidebar: () => void;
    clearChat: () => void;
    openSettings: () => void;
    onLogout: () => void;
    sidebarVisible?: boolean;
}

const Header = ({
    toggleSidebar,
    clearChat,
    openSettings,
    onLogout,
    sidebarVisible = true,
}: HeaderProps) => {
    const [dropdownVisible, setDropdownVisible] = useState(false);
    const [showClearChatConfirm, setShowClearChatConfirm] = useState(false);
    const dropdownRef = useRef<HTMLDivElement>(null);
    const avatarRef = useRef<HTMLDivElement>(null);
    const { activeConversation, conversations } = useChat();
    const { user, logout } = useAuth();
    const { settings, updateSettings } = useSettings();
    const [windowWidth, setWindowWidth] = useState<number>(1200);

    // Theo dõi kích thước màn hình
    useEffect(() => {
        const handleResize = () => {
            setWindowWidth(window.innerWidth);
        };

        if (typeof window !== "undefined") {
            setWindowWidth(window.innerWidth);
            window.addEventListener("resize", handleResize);
        }

        return () => {
            if (typeof window !== "undefined") {
                window.removeEventListener("resize", handleResize);
            }
        };
    }, []);

    // Tìm tên của hội thoại hiện tại
    const currentConversation = conversations.find(
        (conv) => conv.id === activeConversation
    );
    const conversationName = currentConversation?.name || "Cuộc trò chuyện mới";

    // Hàm xử lý tên cuộc hội thoại quá dài
    const formatConversationName = (name: string) => {
        // Điều chỉnh độ dài tùy theo kích thước màn hình
        let maxLength = 30;
        if (windowWidth <= 768) maxLength = 20;
        if (windowWidth <= 480) maxLength = 15;

        return name.length > maxLength
            ? name.substring(0, maxLength) + "..."
            : name;
    };

    // Xử lý sự kiện click bên ngoài dropdown để đóng dropdown
    const handleClickOutside = useCallback((event: MouseEvent) => {
        if (
            dropdownRef.current &&
            avatarRef.current &&
            !dropdownRef.current.contains(event.target as Node) &&
            !avatarRef.current.contains(event.target as Node)
        ) {
            setDropdownVisible(false);
        }
    }, []);

    // Đăng ký sự kiện mousedown trên document
    useEffect(() => {
        document.addEventListener("mousedown", handleClickOutside);
        return () => {
            document.removeEventListener("mousedown", handleClickOutside);
        };
    }, [handleClickOutside]);

    const toggleDropdown = (e: React.MouseEvent) => {
        e.stopPropagation(); // Ngăn sự kiện lan truyền
        setDropdownVisible(!dropdownVisible);
    };

    const toggleDarkMode = () => {
        updateSettings("darkMode", !settings.darkMode);
    };

    const handleClearChat = () => {
        setShowClearChatConfirm(true);
        setDropdownVisible(false);
    };

    const confirmClearChat = () => {
        clearChat();
        setShowClearChatConfirm(false);
    };

    const cancelClearChat = () => {
        setShowClearChatConfirm(false);
    };

    const handleOpenSettings = () => {
        openSettings();
        setDropdownVisible(false);
    };

    const handleLogout = () => {
        onLogout();
        setDropdownVisible(false);
    };

    return (
        <>
            <div className={styles.mainHeader}>
                <button
                    className={styles.toggleSidebarBtn}
                    onClick={() => {
                        console.log("Toggle sidebar button clicked in Header");
                        toggleSidebar();
                    }}
                    aria-label={
                        sidebarVisible ? "Ẩn thanh bên" : "Hiện thanh bên"
                    }
                    style={{ display: "flex" }}
                >
                    {sidebarVisible ? <FaAngleLeft /> : <FaBars />}
                </button>

                <h1
                    className={styles.mainTitle}
                    title={conversationName}
                    style={{
                        overflow: "hidden",
                        textOverflow: "ellipsis",
                        whiteSpace: "nowrap",
                        maxWidth: windowWidth <= 480 ? "150px" : "300px",
                    }}
                >
                    {formatConversationName(conversationName)}
                </h1>

                <div className={styles.userMenuContainer}>
                    <div className={styles.userActions}>
                        <button
                            onClick={handleClearChat}
                            title="Xóa cuộc trò chuyện hiện tại"
                        >
                            <FaEraser />
                        </button>
                        <button
                            onClick={toggleDarkMode}
                            title={
                                settings.darkMode ? "Chế độ sáng" : "Chế độ tối"
                            }
                        >
                            {settings.darkMode ? <FaSun /> : <FaMoon />}
                        </button>
                        <button onClick={handleOpenSettings} title="Cài đặt">
                            <FaCog />
                        </button>
                    </div>

                    <div className={styles.userAvatar}>
                        <div
                            onClick={toggleDropdown}
                            ref={avatarRef}
                            title="Menu người dùng"
                            className={
                                dropdownVisible ? styles.avatarActive : ""
                            }
                        >
                            <Image
                                src={
                                    user?.picture ||
                                    "https://ui-avatars.com/api/?name=User&background=3498db&color=fff"
                                }
                                alt="User Avatar"
                                width={40}
                                height={40}
                            />
                        </div>

                        <div
                            className={`${styles.userDropdown} ${
                                dropdownVisible ? styles.active : ""
                            }`}
                            ref={dropdownRef}
                        >
                            <div className={styles.userInfo}>
                                <Image
                                    src={
                                        user?.picture ||
                                        "https://ui-avatars.com/api/?name=User&background=3498db&color=fff"
                                    }
                                    alt="User Avatar"
                                    width={40}
                                    height={40}
                                />
                                <div className={styles.userDetails}>
                                    <div className={styles.userName}>
                                        {user?.displayName || "Người dùng"}
                                    </div>
                                    <div className={styles.userEmail}>
                                        {user?.emailAddress ||
                                            "user@hbc.com.vn"}
                                    </div>
                                </div>
                            </div>

                            <div className={styles.dropdownMenu}>
                                <div
                                    className={styles.dropdownItem}
                                    onClick={handleOpenSettings}
                                >
                                    <FaCog />
                                    <span>Cài đặt</span>
                                </div>

                                <div className={styles.dropdownDivider}></div>

                                <div
                                    className={styles.dropdownItem}
                                    onClick={handleLogout}
                                >
                                    <FaSignOutAlt />
                                    <span>Đăng xuất</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <ConfirmDialog
                isOpen={showClearChatConfirm}
                title="Xóa cuộc trò chuyện"
                message="Bạn có chắc chắn muốn xóa tất cả tin nhắn trong cuộc trò chuyện hiện tại không? Hành động này không thể hoàn tác."
                confirmText="Xóa"
                cancelText="Hủy"
                onConfirm={confirmClearChat}
                onCancel={cancelClearChat}
                type="danger"
            />
        </>
    );
};

export default Header;
