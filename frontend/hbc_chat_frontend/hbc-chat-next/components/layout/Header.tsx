import { useState, useEffect, useRef, useCallback } from "react";
import {
    FaCog,
    FaTrash,
    FaSignOutAlt,
    FaBars,
    FaMoon,
    FaSun,
    FaAngleRight,
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
    const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
    const dropdownRef = useRef<HTMLDivElement>(null);
    const avatarRef = useRef<HTMLDivElement>(null);
    const { activeConversation, conversations, loadChatHistoryFromAPI } =
        useChat();
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

    const handleOpenSettings = () => {
        openSettings();
        setDropdownVisible(false);
    };

    const handleLogout = () => {
        onLogout();
        setDropdownVisible(false);
    };

    // Hàm để hiển thị dialog xác nhận xóa phiên chat
    const handleShowDeleteConfirm = () => {
        setShowDeleteConfirm(true);
        setDropdownVisible(false);
    };

    // Hàm gọi API xóa phiên chat
    const handleDeleteChatSession = async () => {
        if (!activeConversation || !currentConversation) {
            setShowDeleteConfirm(false);
            return;
        }

        try {
            // Lấy token xác thực từ cookie
            const getCookie = (name: string) => {
                const value = `; ${document.cookie}`;
                const parts = value.split(`; ${name}=`);
                if (parts.length === 2) return parts.pop()?.split(";").shift();
                return null;
            };

            const accessToken = getCookie("access_token");
            if (!accessToken) {
                alert("Vui lòng đăng nhập lại");
                return;
            }

            // Lấy thông tin cần thiết để gửi API
            const topic = settings.aiTopic; // Sử dụng giá trị từ settings
            const sessionName = currentConversation.name;
            const userEmail = user?.emailAddress || "";

            // Gọi API xóa phiên chat
            const response = await fetch(
                `https://aiapi.hbc.com.vn/api/chat/delete?topic=${encodeURIComponent(
                    topic
                )}&user_email=${encodeURIComponent(
                    userEmail
                )}&session_name=${encodeURIComponent(sessionName)}`,
                {
                    method: "DELETE",
                    headers: {
                        Authorization: `Bearer ${accessToken}`,
                        "Content-Type": "application/json",
                    },
                }
            );

            if (response.ok) {
                // Nếu xóa thành công, cập nhật lại danh sách chat
                await loadChatHistoryFromAPI();
                setShowDeleteConfirm(false);
            } else {
                console.error("Lỗi khi xóa phiên chat:", response.statusText);
                alert("Xóa phiên chat không thành công. Vui lòng thử lại sau.");
                setShowDeleteConfirm(false);
            }
        } catch (error) {
            console.error("Lỗi khi xóa phiên chat:", error);
            alert("Đã xảy ra lỗi khi xóa phiên chat.");
            setShowDeleteConfirm(false);
        }
    };

    const cancelDeleteChat = () => {
        setShowDeleteConfirm(false);
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
                            onClick={handleShowDeleteConfirm}
                            title="Xóa phiên chat hiện tại"
                        >
                            <FaTrash />
                        </button>
                        <button
                            onClick={toggleDarkMode}
                            title={
                                settings.darkMode ? "Chế độ sáng" : "Chế độ tối"
                            }
                        >
                            {settings.darkMode ? <FaSun /> : <FaMoon />}
                        </button>
                        {/* Nút setting đã bị ẩn theo yêu cầu */}
                        {/* <button onClick={handleOpenSettings} title="Cài đặt">
                            <FaCog />
                        </button> */}
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
                isOpen={showDeleteConfirm}
                title="Xóa phiên chat"
                message="Bạn có chắc chắn muốn xóa phiên chat hiện tại? Hành động này không thể hoàn tác."
                confirmText="Xóa"
                cancelText="Hủy"
                onConfirm={handleDeleteChatSession}
                onCancel={cancelDeleteChat}
                type="danger"
            />
        </>
    );
};

export default Header;
