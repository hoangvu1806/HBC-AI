import { useState, useEffect } from "react";
import Image from "next/image";
import {
    FaPlus,
    FaCommentDots,
    FaEdit,
    FaClock,
    FaStar,
    FaAngleLeft,
} from "react-icons/fa";
import styles from "@/styles/Sidebar.module.css";

interface Conversation {
    id: string;
    name: string;
    messages?: any[]; // Thêm messages để phù hợp với interface trong ChatContext
}

interface SidebarProps {
    conversations: Conversation[];
    activeConversation: string;
    onNewChat: () => void;
    onSelectChat: (id: string) => void;
    onDeleteChat: (id: string) => void;
    onRenameChat: (id: string, newName: string) => void;
    isVisible?: boolean;
    onCloseSidebar?: () => void;
    style?: React.CSSProperties;
}

const Sidebar = ({
    conversations,
    activeConversation,
    onNewChat,
    onSelectChat,
    onDeleteChat,
    onRenameChat,
    isVisible = true,
    onCloseSidebar,
    style,
}: SidebarProps) => {
    const [editingId, setEditingId] = useState<string | null>(null);
    const [editName, setEditName] = useState("");
    const [animatedItems, setAnimatedItems] = useState<boolean>(false);

    // Hàm cắt tên cuộc hội thoại nếu quá dài
    const truncateConversationName = (name: string, maxLength = 18) => {
        return name.length > maxLength
            ? name.substring(0, maxLength) + "..."
            : name;
    };

    // Kích hoạt animation cho các mục
    useEffect(() => {
        const timer = setTimeout(() => {
            setAnimatedItems(true);
        }, 300);

        return () => clearTimeout(timer);
    }, []);

    const handleEditClick = (
        id: string,
        currentName: string,
        e: React.MouseEvent
    ) => {
        e.stopPropagation();
        setEditingId(id);
        setEditName(currentName);
    };

    const handleRenameSubmit = (id: string, e: React.FormEvent) => {
        e.preventDefault();
        if (editName.trim()) {
            onRenameChat(id, editName);
            setEditingId(null);
        }
    };

    // Sử dụng cùng một icon cho tất cả các cuộc hội thoại
    const getConversationIcon = (id: string) => {
        return <FaCommentDots />;
    };

    return (
        <>
            <div
                className={styles.sidebar}
                style={{
                    boxShadow: isVisible
                        ? "2px 0 10px rgba(0, 0, 0, 0.05)"
                        : "none",
                    ...style,
                }}
            >
                <div className={styles.sidebarHeader}>
                    {onCloseSidebar && (
                        <button
                            className={styles.closeSidebarBtn}
                            onClick={onCloseSidebar}
                            aria-label="Đóng menu"
                        >
                            <FaAngleLeft />
                        </button>
                    )}
                    <div className={styles.companyLogo}>
                        <Image
                            src="/logo-HBC.png"
                            alt="HBC Logo"
                            width={125}
                            height={60}
                        />
                    </div>
                    <button
                        className={styles.newChatBtn}
                        onClick={(e) => {
                            e.preventDefault();
                            console.log("Đang gọi onNewChat...");
                            onNewChat();
                        }}
                    >
                        <FaPlus /> <span>Hội thoại mới</span>
                    </button>
                </div>

                <div className={styles.conversationsList}>
                    {conversations.length === 0 ? (
                        <div className={styles.noConversations}>
                            Chưa có hội thoại nào. Bắt đầu bằng cách tạo hội
                            thoại mới.
                        </div>
                    ) : (
                        conversations.map((conv, index) => (
                            <div
                                key={conv.id}
                                className={`${styles.conversationItem} ${
                                    activeConversation === conv.id
                                        ? styles.active
                                        : ""
                                } ${animatedItems ? styles.animated : ""}`}
                                onClick={() => onSelectChat(conv.id)}
                                style={{
                                    animationDelay: `${index * 0.05}s`,
                                    opacity: animatedItems ? 1 : 0,
                                    transform: animatedItems
                                        ? "translateX(0)"
                                        : "translateX(-20px)",
                                }}
                                title={conv.name}
                            >
                                {getConversationIcon(conv.id)}
                                {editingId === conv.id ? (
                                    <form
                                        onSubmit={(e) =>
                                            handleRenameSubmit(conv.id, e)
                                        }
                                        className={styles.conversationName}
                                    >
                                        <input
                                            type="text"
                                            value={editName}
                                            onChange={(e) =>
                                                setEditName(e.target.value)
                                            }
                                            autoFocus
                                            onBlur={() => setEditingId(null)}
                                            placeholder="Nhập tên hội thoại"
                                        />
                                    </form>
                                ) : (
                                    <span className={styles.conversationName}>
                                        {truncateConversationName(conv.name)}
                                    </span>
                                )}
                                <div className={styles.conversationActions}>
                                    <button
                                        className={styles.editNameBtn}
                                        title="Chỉnh sửa tên"
                                        onClick={(e) =>
                                            handleEditClick(
                                                conv.id,
                                                conv.name,
                                                e
                                            )
                                        }
                                    >
                                        <FaEdit />
                                    </button>
                                </div>
                            </div>
                        ))
                    )}
                </div>

                <div className={styles.sidebarFooter}>
                    © {new Date().getFullYear()} HBC AI Assistant
                </div>
            </div>
        </>
    );
};

export default Sidebar;
