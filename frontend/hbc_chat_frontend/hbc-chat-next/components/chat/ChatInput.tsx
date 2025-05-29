import { useState, useRef, useEffect } from "react";
import { FaPaperPlane, FaLightbulb, FaSpinner } from "react-icons/fa";
import styles from "@/styles/Chat.module.css";

interface ChatInputProps {
    onSendMessage: (message: string) => void;
    isThinkModeActive: boolean;
    toggleThinkMode: () => void;
    isWaitingResponse: boolean;
    aiTopic: string;
}

const ChatInput = ({
    onSendMessage,
    isThinkModeActive,
    toggleThinkMode,
    isWaitingResponse,
    aiTopic,
}: ChatInputProps) => {
    const [message, setMessage] = useState("");
    const textareaRef = useRef<HTMLTextAreaElement>(null);
    const [windowWidth, setWindowWidth] = useState<number>(
        typeof window !== "undefined" ? window.innerWidth : 1200
    );

    // Theo dõi kích thước cửa sổ
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

    // Hàm xử lý placeholder theo kích thước màn hình
    const getPlaceholder = () => {
        const waitingText = "Đang xử lý câu trả lời...";
        const normalText = "Nhập tin nhắn của bạn...";

        if (windowWidth <= 480) {
            return isWaitingResponse ? "Đang xử lý..." : "Nhập tin nhắn...";
        }

        return isWaitingResponse ? waitingText : normalText;
    };

    // Auto-resize textarea as user types
    useEffect(() => {
        if (textareaRef.current) {
            textareaRef.current.style.height = "auto";
            textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
        }
    }, [message]);

    const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
        setMessage(e.target.value);
    };

    const handleSendMessage = () => {
        if (message.trim() && !isWaitingResponse) {
            onSendMessage(message);
            setMessage("");
            // Reset textarea height
            if (textareaRef.current) {
                textareaRef.current.style.height = "auto";
            }
        }
    };

    const handleKeyDown = (e: React.KeyboardEvent) => {
        // Send message on Enter (without Shift) if not waiting for response
        if (e.key === "Enter" && !e.shiftKey && !isWaitingResponse) {
            e.preventDefault();
            handleSendMessage();
        }
    };

    return (
        <div className={styles.chatInputWrapper}>
            <div className={styles.chatInputContainer}>
                <div className={styles.chatTools}>
                    {aiTopic !== "NGHI_PHEP" && (
                        <button
                            className={`${styles.thinkToggleBtn} ${
                                isThinkModeActive ? styles.active : ""
                            }`}
                            title={
                                isThinkModeActive
                                    ? "Tắt chế độ suy nghĩ"
                                    : "Bật chế độ suy nghĩ"
                            }
                            onClick={toggleThinkMode}
                            aria-pressed={isThinkModeActive}
                        >
                            <FaLightbulb />
                            <span>Suy luận</span>
                        </button>
                    )}
                </div>

                <textarea
                    ref={textareaRef}
                    className={styles.textarea}
                    value={message}
                    onChange={handleInputChange}
                    onKeyDown={handleKeyDown}
                    placeholder={getPlaceholder()}
                    rows={1}
                />

                <button
                    className={styles.sendBtn}
                    onClick={handleSendMessage}
                    title={isWaitingResponse ? "Đang xử lý..." : "Gửi tin nhắn"}
                    disabled={!message.trim() || isWaitingResponse}
                >
                    {isWaitingResponse ? (
                        <FaSpinner
                            className={`${styles.spinnerIcon} ${styles.pulsing}`}
                        />
                    ) : (
                        <FaPaperPlane className={styles.sendIcon} />
                    )}
                </button>
            </div>
        </div>
    );
};

export default ChatInput;
