import { useState, useEffect, useRef } from "react";
import { marked } from "marked";
import hljs from "highlight.js";
import styles from "@/styles/Chat.module.css";
import markdownStyles from "@/styles/Markdown.module.css";
import { useChat } from "@/contexts/ChatContext";

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
    showRating?: boolean;
    onRate?: (rating: number) => void;
    id?: string;
}

const Message = ({
    content,
    isUser,
    timestamp,
    hasFiles = false,
    showRating = false,
    onRate,
    id,
}: MessageProps) => {
    const [rating, setRating] = useState(0);
    const [submitted, setSubmitted] = useState(false);
    const markdownRef = useRef<HTMLDivElement>(null);
    const { messages, isWaitingResponse, isThinkModeActive } = useChat();

    // Kiểm tra xem có cần hiển thị hiệu ứng typing hay không
    // Hiệu ứng chỉ hiển thị khi đang đợi phản hồi và tin nhắn cuối cùng là của người dùng
    const isLastMessage =
        messages.length > 0 && messages[messages.length - 1].id === id;
    const showTypingIndicator = isWaitingResponse && isLastMessage && isUser;

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

    const handleRate = (score: number) => {
        setRating(score);
        if (onRate) {
            onRate(score);
            setSubmitted(true);

            // Reset the submitted state after a few seconds
            setTimeout(() => {
                setSubmitted(false);
            }, 3000);
        }
    };

    return (
        <>
            <div
                className={`${styles.message} ${
                    isUser ? styles.user : styles.bot
                }`}
            >
                <div className={styles.messageContent}>
                    {isUser ? (
                        <div>{content}</div>
                    ) : (
                        <div
                            ref={markdownRef}
                            className={`${markdownStyles.markdownContent} ${
                                hasFiles ? markdownStyles.hasFiles : ""
                            }`}
                            dangerouslySetInnerHTML={{
                                __html: marked.parse(content),
                            }}
                        />
                    )}
                </div>

                <div className={styles.messageTime}>
                    {formatTime(timestamp)}

                    {!isUser && showRating && (
                        <div className={styles.messageRating}>
                            {!submitted ? (
                                <>
                                    <div className={styles.messageRatingLabel}>
                                        Đánh giá hữu ích?
                                    </div>
                                    <div className={styles.ratingStars}>
                                        {[1, 2, 3, 4, 5].map((star) => (
                                            <span
                                                key={star}
                                                className={`${
                                                    styles.ratingStar
                                                } ${
                                                    rating >= star
                                                        ? styles.active
                                                        : ""
                                                }`}
                                                onClick={() => handleRate(star)}
                                            />
                                        ))}
                                    </div>
                                </>
                            ) : (
                                <div
                                    className={`${styles.ratingSubmitted} ${styles.show}`}
                                >
                                    Cảm ơn bạn đã đánh giá!
                                </div>
                            )}
                        </div>
                    )}
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
        </>
    );
};

export default Message;
