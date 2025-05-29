import { useState, useEffect, useRef } from "react";
import { marked } from "marked";
import hljs from "highlight.js";
import styles from "@/styles/Chat.module.css";
import markdownStyles from "@/styles/Markdown.module.css";
import { useChat } from "@/contexts/ChatContext";
import SuggestEditModal from "../ui/SuggestEditModal";

// Configure marked with highlight.js and fix TypeScript compatibility issues
const renderer = {
    code(code: string, language: string | undefined) {
        const validLanguage = hljs.getLanguage(language || "")
            ? language
            : "plaintext";
        // Sửa cách gọi hàm highlight theo API mới của highlight.js 11.x
        // API cũ: hljs.highlight(code, { language: lang })
        // API mới: hljs.highlight(code, { language: lang }).value
        // hoặc: hljs.highlight(code, lang).value
        try {
            return `<pre class="hljs-pre"><code class="hljs ${validLanguage}">${
                hljs.highlight(code, { language: validLanguage || "plaintext" })
                    .value
            }</code></pre>`;
        } catch (error) {
            // Fallback nếu có lỗi với cú pháp API mới
            try {
                // Thử với cú pháp API cũ hơn
                return `<pre class="hljs-pre"><code class="hljs ${validLanguage}">${
                    hljs.highlight(validLanguage || "plaintext", code).value
                }</code></pre>`;
            } catch (fallbackError) {
                // Fallback cuối cùng nếu cả hai đều không hoạt động
                console.error("Highlight.js error:", error);
                return `<pre class="hljs-pre"><code class="hljs">${code}</code></pre>`;
            }
        }
    },
};

marked.use({
    gfm: true,
    breaks: true,
    renderer: renderer as any, // Type cast để tránh lỗi TypeScript
});

interface MessageProps {
    content: string;
    isUser: boolean;
    timestamp: Date;
    hasFiles?: boolean;
    id?: string;
}

const Message = ({
    content,
    isUser,
    timestamp,
    hasFiles = false,
    id,
}: MessageProps) => {
    const markdownRef = useRef<HTMLDivElement>(null);
    const { messages, isWaitingResponse, isThinkModeActive, sendMessage } =
        useChat();
    const [showOptions, setShowOptions] = useState(false);
    const [copySuccess, setCopySuccess] = useState(false);
    const [showTooltip, setShowTooltip] = useState("");
    const [showEditModal, setShowEditModal] = useState(false);

    // Kiểm tra xem có cần hiển thị hiệu ứng typing hay không
    // Hiệu ứng chỉ hiển thị khi đang đợi phản hồi và tin nhắn cuối cùng là của người dùng
    const isLastMessage =
        messages.length > 0 && messages[messages.length - 1].id === id;
    const showTypingIndicator = isWaitingResponse && isLastMessage && isUser;
    
    // Kiểm tra xem có hiển thị hiệu ứng chờ khi bot chưa trả lời hoặc tin nhắn trống
    const isEmptyBotMessage = !isUser && content === '' && isWaitingResponse;
    const showStreamWaitingIndicator = isEmptyBotMessage;

    useEffect(() => {
        // Apply syntax highlighting to code blocks
        if (markdownRef.current) {
            const codeBlocks = markdownRef.current.querySelectorAll("pre code");
            codeBlocks.forEach((block) => {
                try {
                    // Sử dụng API mới của highlight.js 11.x
                    hljs.highlightElement(block as HTMLElement);
                } catch (error) {
                    console.error(
                        "Highlight.js highlightElement error:",
                        error
                    );
                    // Fallback: Thử lại với cách thực hiện thủ công
                    try {
                        const code = block.textContent || "";
                        const language = (block.className.match(
                            /language-(\w+)/
                        ) || [null, "plaintext"])[1];
                        if (code) {
                            block.innerHTML = hljs.highlight(code, {
                                language,
                            }).value;
                        }
                    } catch (fallbackError) {
                        console.error(
                            "Highlight.js manual highlight error:",
                            fallbackError
                        );
                    }
                }
            });
        }
    }, [content]);

    const formatTime = (date: Date) => {
        // Kiểm tra nếu date không phải đối tượng Date hoặc là null/undefined
        if (!date || !(date instanceof Date) || isNaN(date.getTime())) {
            try {
                // Thử chuyển đổi thành đối tượng Date
                const parsedDate = new Date(date);
                if (!isNaN(parsedDate.getTime())) {
                    return parsedDate.toLocaleTimeString("vi-VN", {
                        hour: "2-digit",
                        minute: "2-digit",
                    });
                }
                // Nếu không chuyển đổi được, trả về thời gian hiện tại
                return new Date().toLocaleTimeString("vi-VN", {
                    hour: "2-digit",
                    minute: "2-digit",
                });
            } catch (e) {
                // Nếu có lỗi, trả về thời gian hiện tại
                return new Date().toLocaleTimeString("vi-VN", {
                    hour: "2-digit",
                    minute: "2-digit",
                });
            }
        }

        // Nếu là đối tượng Date hợp lệ
        return date.toLocaleTimeString("vi-VN", {
            hour: "2-digit",
            minute: "2-digit",
        });
    };

    const handleCopyMessage = () => {
        const textToCopy = isUser
            ? content
            : markdownRef.current?.textContent || content;

        // Kiểm tra xem trình duyệt có hỗ trợ Clipboard API không
        if (navigator.clipboard && navigator.clipboard.writeText) {
            navigator.clipboard
                .writeText(textToCopy)
                .then(() => {
                    setCopySuccess(true);
                    setShowTooltip("Đã sao chép!");
                    setTimeout(() => {
                        setCopySuccess(false);
                        setShowTooltip("");
                    }, 2000);
                    console.log("Đã sao chép vào bộ nhớ tạm");
                })
                .catch((err) => {
                    console.error("Lỗi khi sao chép: ", err);
                    setShowTooltip("Không thể sao chép!");
                    setTimeout(() => setShowTooltip(""), 2000);
                });
        } else {
            // Fallback nếu trình duyệt không hỗ trợ Clipboard API
            try {
                // Tạo một element để sao chép văn bản
                const textArea = document.createElement("textarea");
                textArea.value = textToCopy;
                textArea.style.position = "fixed"; // Tránh làm scroll trang
                document.body.appendChild(textArea);
                textArea.focus();
                textArea.select();

                // Thử sử dụng document.execCommand('copy') - API cũ
                const successful = document.execCommand("copy");
                if (successful) {
                    setCopySuccess(true);
                    setShowTooltip("Đã sao chép!");
                    setTimeout(() => {
                        setCopySuccess(false);
                        setShowTooltip("");
                    }, 2000);
                    console.log("Đã sao chép vào bộ nhớ tạm (fallback)");
                } else {
                    setShowTooltip("Không thể sao chép!");
                    setTimeout(() => setShowTooltip(""), 2000);
                }

                // Dọn dẹp
                document.body.removeChild(textArea);
            } catch (err) {
                console.error("Lỗi khi sao chép (fallback): ", err);
                setShowTooltip("Không thể sao chép!");
                setTimeout(() => setShowTooltip(""), 2000);
            }
        }
    };

    // Tìm tin nhắn người dùng trước đó
    const findPreviousUserMessage = () => {
        if (!id || isUser) return "";

        // Tìm index của tin nhắn hiện tại
        const currentIndex = messages.findIndex((msg) => msg.id === id);
        if (currentIndex <= 0) return "";

        // Tìm tin nhắn người dùng gần nhất trước tin nhắn hiện tại
        for (let i = currentIndex - 1; i >= 0; i--) {
            if (messages[i].isUser) {
                return messages[i].content;
            }
        }

        return "";
    };

    const handleSuggestEdit = () => {
        // Hiển thị modal đề xuất chỉnh sửa
        setShowEditModal(true);
    };

    const handleCancelEdit = () => {
        setShowEditModal(false);
    };

    const handleSubmitEdit = (suggestedContent: string) => {
        // Gửi nội dung đề xuất phản hồi
        if (suggestedContent.trim()) {
            const previousQuery = findPreviousUserMessage();
            let message = `Đề xuất phản hồi:`;

            // Thêm câu hỏi của người dùng nếu có
            if (previousQuery) {
                message += `\n\n**Câu hỏi ban đầu của tôi:**\n${previousQuery}`;
            }

            // Thêm phản hồi đề xuất
            message += `\n\n**Phản hồi đề xuất:**\n${suggestedContent}`;

            sendMessage(message);
            setShowEditModal(false);
        }
    };

    return (
        <>
            <div
                className={`${styles.message} ${
                    isUser ? styles.user : styles.bot
                }`}
                onMouseEnter={() => setShowOptions(true)}
                onMouseLeave={() => setShowOptions(false)}
            >
                <div className={styles.messageContent}>
                    {isUser ? (
                        <div>{content}</div>
                    ) : (
                        <div
                            ref={markdownRef}
                            className={`${markdownStyles.markdownContent} ${
                                hasFiles ? markdownStyles.hasFiles : ""
                            } ${content.includes("Phiên làm việc đã hết hạn") ? styles.sessionExpiredMessage : ""}`}
                            dangerouslySetInnerHTML={{
                                __html: content ? marked.parse(content) : '',
                            }}
                        />
                    )}

                    {/* Hiển thị hiệu ứng đợi stream nếu tin nhắn bot trống */}
                    {showStreamWaitingIndicator && (
                        <div className={styles.typingIndicator}>
                            <span></span>
                            <span></span>
                            <span></span>
                        </div>
                    )}

                    {showOptions && (
                        <div className={styles.messageOptions}>
                            {showTooltip && (
                                <div className={styles.tooltip}>
                                    {showTooltip}
                                </div>
                            )}
                            <button
                                className={styles.optionButton}
                                onClick={handleCopyMessage}
                                title="Sao chép"
                            >
                                {copySuccess ? (
                                    <svg
                                        xmlns="http://www.w3.org/2000/svg"
                                        width="16"
                                        height="16"
                                        viewBox="0 0 24 24"
                                        fill="none"
                                        stroke="currentColor"
                                        strokeWidth="2"
                                        strokeLinecap="round"
                                        strokeLinejoin="round"
                                    >
                                        <path d="M20 6L9 17l-5-5"></path>
                                    </svg>
                                ) : (
                                    <svg
                                        xmlns="http://www.w3.org/2000/svg"
                                        width="16"
                                        height="16"
                                        viewBox="0 0 24 24"
                                        fill="none"
                                        stroke="currentColor"
                                        strokeWidth="2"
                                        strokeLinecap="round"
                                        strokeLinejoin="round"
                                    >
                                        <rect
                                            x="9"
                                            y="9"
                                            width="13"
                                            height="13"
                                            rx="2"
                                            ry="2"
                                        ></rect>
                                        <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
                                    </svg>
                                )}
                            </button>
                            {!isUser && (
                                <button
                                    className={styles.optionButton}
                                    onClick={handleSuggestEdit}
                                    title="Đề xuất phản hồi"
                                >
                                    <svg
                                        xmlns="http://www.w3.org/2000/svg"
                                        width="16"
                                        height="16"
                                        viewBox="0 0 24 24"
                                        fill="none"
                                        stroke="currentColor"
                                        strokeWidth="2"
                                        strokeLinecap="round"
                                        strokeLinejoin="round"
                                    >
                                        <path d="M17 3a2.85 2.85 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5L17 3z"></path>
                                    </svg>
                                </button>
                            )}
                        </div>
                    )}
                </div>

                <div className={styles.messageTime}>
                    {formatTime(timestamp)}
                </div>
            </div>

            {/* Hiển thị hiệu ứng typing sau tin nhắn của người dùng */}
            {showTypingIndicator && (
                <div className={styles.typingIndicatorContainer}>
                    <div className={styles.typingIndicatorContent}>
                        <div className={styles.typingIndicator}>
                            <span></span>
                            <span></span>
                            <span></span>
                        </div>
                        <div className={styles.typingIndicatorText}>
                            {isThinkModeActive
                                ? "Đang suy nghĩ..."
                                : "Đang viết..."}
                        </div>
                    </div>
                </div>
            )}

            {/* Modal đề xuất chỉnh sửa */}
            <SuggestEditModal
                isOpen={showEditModal}
                originalContent={content}
                previousUserQuery={findPreviousUserMessage()}
                onCancel={handleCancelEdit}
                onSubmit={handleSubmitEdit}
            />
        </>
    );
};

export default Message;
