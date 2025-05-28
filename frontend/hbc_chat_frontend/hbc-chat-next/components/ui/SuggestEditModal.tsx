import React, { useEffect, useRef, useState } from "react";
import { IoMdClose } from "react-icons/io";
import { FiEdit3, FiMessageSquare } from "react-icons/fi";

interface SuggestEditModalProps {
    isOpen: boolean;
    originalContent: string;
    previousUserQuery: string;
    onCancel: () => void;
    onSubmit: (suggestedContent: string) => void;
}

const SuggestEditModal: React.FC<SuggestEditModalProps> = ({
    isOpen,
    originalContent,
    previousUserQuery,
    onCancel,
    onSubmit,
}) => {
    const modalRef = useRef<HTMLDivElement>(null);
    const textareaRef = useRef<HTMLTextAreaElement>(null);
    const [suggestedContent, setSuggestedContent] = useState("");
    const [isClosing, setIsClosing] = useState(false);
    const [highlightChanges, setHighlightChanges] = useState(false);

    // Thiết lập nội dung ban đầu là nội dung cũ khi modal mở
    useEffect(() => {
        if (isOpen) {
            setSuggestedContent(originalContent);
            setIsClosing(false);
        }
    }, [isOpen, originalContent]);

    useEffect(() => {
        // Focus vào textarea khi modal mở và đặt con trỏ vào cuối văn bản
        if (isOpen && textareaRef.current) {
            textareaRef.current.focus();
            const length = textareaRef.current.value.length;
            textareaRef.current.setSelectionRange(length, length);
        }
    }, [isOpen]);

    const closeWithAnimation = () => {
        setIsClosing(true);
        setTimeout(() => {
            onCancel();
        }, 300); // Thời gian chạy animation
    };

    useEffect(() => {
        const handleClickOutside = (event: MouseEvent) => {
            if (
                modalRef.current &&
                !modalRef.current.contains(event.target as Node)
            ) {
                closeWithAnimation();
            }
        };

        const handleEscKey = (event: KeyboardEvent) => {
            if (event.key === "Escape") {
                closeWithAnimation();
            }
        };

        if (isOpen) {
            document.addEventListener("mousedown", handleClickOutside);
            document.addEventListener("keydown", handleEscKey);
            // Vô hiệu hóa cuộn trang khi modal hiện
            document.body.style.overflow = "hidden";
        }

        return () => {
            document.removeEventListener("mousedown", handleClickOutside);
            document.removeEventListener("keydown", handleEscKey);
            // Khôi phục cuộn trang khi modal đóng
            document.body.style.overflow = "auto";
        };
    }, [isOpen, onCancel]);

    // Hàm lấy cookie
    const getCookie = (name: string): string | null => {
        if (typeof document === "undefined") return null;
        const value = `; ${document.cookie}`;
        const parts = value.split(`; ${name}=`);
        if (parts.length === 2) return parts.pop()?.split(";").shift() || null;
        return null;
    };

    const handleSubmit = async () => {
        if (suggestedContent.trim()) {
            try {
                // Thêm hiệu ứng ripple khi nhấn nút
                const rippleEffect = document.createElement("span");
                rippleEffect.classList.add("ripple");
                document
                    .querySelector(".suggest-edit-submit")
                    ?.appendChild(rippleEffect);

                // Lấy thông tin người dùng và phiên hiện tại
                let userEmail = "guest";
                const userData = localStorage.getItem("user");
                if (userData) {
                    const parsedUser = JSON.parse(userData);
                    userEmail = parsedUser.emailAddress || "guest";
                }

                // Lấy tên hội thoại
                let sessionName = "Cuộc trò chuyện mới";
                const activeConversation =
                    localStorage.getItem("activeConversation");
                if (activeConversation) {
                    const conversations = JSON.parse(
                        localStorage.getItem("conversations") || "[]"
                    );
                    const currentConv = conversations.find(
                        (conv: any) => conv.id === activeConversation
                    );
                    if (currentConv) {
                        sessionName = currentConv.name;
                    }
                }

                // Lấy token xác thực
                const accessToken = getCookie("access_token");
                if (!accessToken) {
                    throw new Error("Không tìm thấy access token");
                }

                // Chuẩn bị dữ liệu feedback
                const feedbackData = {
                    user_email: userEmail,
                    topic: "HCNS",
                    session_name: sessionName,
                    question: previousUserQuery,
                    initial_response: originalContent,
                    suggest_response: suggestedContent,
                };

                // Hiển thị trạng thái đang gửi
                const submitButton = document.querySelector(
                    ".suggest-edit-submit"
                );
                if (submitButton) {
                    const buttonText =
                        submitButton.querySelector(".button-text");
                    if (buttonText) {
                        const originalText =
                            buttonText.textContent || "Đề xuất";
                        buttonText.textContent = "Đang gửi...";
                    }
                    (submitButton as HTMLButtonElement).disabled = true;
                }

                // Sử dụng API proxy để tránh vấn đề CORS
                const proxyResponse = await fetch("/api/feedback-proxy", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                    },
                    body: JSON.stringify({
                        ...feedbackData,
                        token: accessToken,
                    }),
                });

                const proxyResultText = await proxyResponse.text();
                let proxyResult;
                try {
                    proxyResult = JSON.parse(proxyResultText);
                } catch (e) {
                    proxyResult = { success: false, message: proxyResultText };
                }

                // Restore button state
                if (submitButton) {
                    const buttonText =
                        submitButton.querySelector(".button-text");
                    if (buttonText) {
                        buttonText.textContent = "Đề xuất";
                    }
                    (submitButton as HTMLButtonElement).disabled = false;
                }

                if (!proxyResponse.ok) {
                    throw new Error(
                        `Lỗi khi gửi feedback: ${
                            proxyResult.message || proxyResponse.status
                        }`
                    );
                }

                // Hiển thị thông báo thành công
                alert("Đã gửi đề xuất phản hồi thành công!");

                // Đóng modal sau khi gửi feedback thành công
                setTimeout(() => {
                    closeWithAnimation();
                }, 300);
            } catch (error: any) {
                console.error("Lỗi khi gửi feedback:", error);
                // Hiển thị thông báo lỗi
                alert(
                    `Có lỗi xảy ra khi gửi đề xuất: ${
                        error.message || "Lỗi không xác định"
                    }`
                );
                // Vẫn đóng modal
                closeWithAnimation();
            }
        }
    };

    // Kiểm tra xem nội dung có thay đổi so với ban đầu không
    const hasChanged = originalContent !== suggestedContent;

    if (!isOpen) return null;

    return (
        <div className={`suggest-edit-overlay ${isClosing ? "closing" : ""}`}>
            <div
                className={`suggest-edit-modal ${isClosing ? "closing" : ""}`}
                ref={modalRef}
            >
                <div className="suggest-edit-header">
                    <div className="suggest-edit-title">
                        <FiMessageSquare className="title-icon" />
                        Đề xuất phản hồi
                    </div>
                    <button
                        className="suggest-edit-close"
                        onClick={closeWithAnimation}
                    >
                        <IoMdClose />
                    </button>
                </div>

                <div className="suggest-edit-content">
                    {previousUserQuery && (
                        <div className="suggest-edit-query">
                            <h3>
                                <span className="pulse-dot"></span>
                                Câu hỏi của bạn:
                            </h3>
                            <div className="user-query animate-in">
                                {previousUserQuery}
                            </div>
                        </div>
                    )}

                    <div className="suggest-edit-input">
                        <h3>
                            <FiEdit3 className="edit-icon" />
                            Chỉnh sửa phản hồi:
                            <div className="toggle-highlight">
                                <label className="toggle">
                                    <input
                                        type="checkbox"
                                        checked={highlightChanges}
                                        onChange={() =>
                                            setHighlightChanges(
                                                !highlightChanges
                                            )
                                        }
                                    />
                                    <span className="slider"></span>
                                </label>
                                <span className="toggle-label">
                                    Đánh dấu thay đổi
                                </span>
                            </div>
                        </h3>
                        <div
                            className={`textarea-wrapper ${
                                hasChanged ? "has-changed" : ""
                            }`}
                        >
                            <textarea
                                ref={textareaRef}
                                value={suggestedContent}
                                onChange={(e) =>
                                    setSuggestedContent(e.target.value)
                                }
                                placeholder="Chỉnh sửa nội dung phản hồi..."
                                rows={12}
                                className={
                                    highlightChanges && hasChanged
                                        ? "highlight-changes"
                                        : ""
                                }
                                data-original-content={
                                    highlightChanges ? originalContent : ""
                                }
                            />

                            {hasChanged && (
                                <div className="change-indicator">
                                    <span className="change-badge">
                                        Đã chỉnh sửa
                                    </span>
                                </div>
                            )}
                        </div>
                        <div className="edit-instructions">
                            <span className="tip-icon">💡</span>
                            Chỉnh sửa trực tiếp nội dung phản hồi ở trên để đề
                            xuất thay đổi
                        </div>
                    </div>
                </div>

                <div className="suggest-edit-actions">
                    <button
                        className="suggest-edit-cancel"
                        onClick={closeWithAnimation}
                    >
                        Hủy
                    </button>
                    <button
                        className="suggest-edit-submit"
                        onClick={handleSubmit}
                        disabled={!suggestedContent.trim() || !hasChanged}
                    >
                        <span className="button-text">Đề xuất</span>
                        {hasChanged && <span className="button-arrow">→</span>}
                    </button>
                </div>
            </div>

            <style jsx>{`
                .suggest-edit-overlay {
                    position: fixed;
                    top: 0;
                    left: 0;
                    right: 0;
                    bottom: 0;
                    background-color: rgba(0, 0, 0, 0.6);
                    backdrop-filter: blur(4px);
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    z-index: 9999;
                    animation: fadeIn 0.4s cubic-bezier(0.16, 1, 0.3, 1);
                    perspective: 1000px;
                }

                .suggest-edit-overlay.closing {
                    animation: fadeOut 0.3s forwards;
                }

                .suggest-edit-modal {
                    background-color: var(--container-bg, #ffffff);
                    border-radius: 16px;
                    width: 700px;
                    max-width: 90vw;
                    max-height: 90vh;
                    box-shadow: 0 10px 40px rgba(0, 0, 0, 0.25),
                        0 1px 10px rgba(0, 0, 0, 0.1),
                        0 0 0 1px rgba(255, 255, 255, 0.1);
                    animation: slideIn 0.4s cubic-bezier(0.16, 1, 0.3, 1);
                    display: flex;
                    flex-direction: column;
                    overflow: hidden;
                    transform-origin: center;
                    border: 1px solid
                        rgba(var(--primary-rgb, 9, 105, 218), 0.15);
                }

                .suggest-edit-modal.closing {
                    animation: slideOut 0.3s forwards;
                }

                .suggest-edit-header {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    padding: 14px 20px;
                    border-bottom: 1px solid var(--border-color, #e1e4e8);
                    background: linear-gradient(
                        to right,
                        var(--container-bg, #ffffff),
                        rgba(var(--primary-rgb, 9, 105, 218), 0.05)
                    );
                }

                .suggest-edit-title {
                    font-weight: 600;
                    font-size: 18px;
                    color: var(--text-color, #24292f);
                    display: flex;
                    align-items: center;
                    gap: 8px;
                }

                .title-icon {
                    color: var(--primary-color, #0969da);
                    animation: pulseScale 2s infinite;
                }

                .edit-icon {
                    color: var(--primary-color, #0969da);
                    margin-right: 6px;
                    animation: rotate 20s linear infinite;
                }

                .suggest-edit-close {
                    background: none;
                    border: none;
                    color: var(--text-secondary, #6e7781);
                    cursor: pointer;
                    font-size: 20px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    padding: 8px;
                    border-radius: 50%;
                    transition: all 0.2s;
                }

                .suggest-edit-close:hover {
                    background-color: var(--hover-color, #f6f8fa);
                    color: var(--text-color, #24292f);
                    transform: rotate(90deg);
                }

                .suggest-edit-content {
                    padding: 18px;
                    flex: 1;
                    overflow-y: auto;
                    display: flex;
                    flex-direction: column;
                    gap: 16px;
                }

                .suggest-edit-query,
                .suggest-edit-input {
                    display: flex;
                    flex-direction: column;
                    gap: 8px;
                }

                .suggest-edit-query h3,
                .suggest-edit-input h3 {
                    font-size: 16px;
                    font-weight: 600;
                    color: var(--text-color, #24292f);
                    margin: 0;
                    display: flex;
                    align-items: center;
                }

                .suggest-edit-input h3 {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    flex-wrap: wrap;
                }

                .toggle-highlight {
                    display: flex;
                    align-items: center;
                    gap: 6px;
                    font-size: 13px;
                    font-weight: normal;
                    color: var(--text-secondary);
                }

                .toggle {
                    position: relative;
                    display: inline-block;
                    width: 36px;
                    height: 20px;
                }

                .toggle input {
                    opacity: 0;
                    width: 0;
                    height: 0;
                }

                .slider {
                    position: absolute;
                    cursor: pointer;
                    top: 0;
                    left: 0;
                    right: 0;
                    bottom: 0;
                    background-color: #ccc;
                    transition: 0.3s;
                    border-radius: 20px;
                }

                .slider:before {
                    position: absolute;
                    content: "";
                    height: 16px;
                    width: 16px;
                    left: 2px;
                    bottom: 2px;
                    background-color: white;
                    transition: 0.3s;
                    border-radius: 50%;
                }

                input:checked + .slider {
                    background-color: var(--primary-color);
                }

                input:checked + .slider:before {
                    transform: translateX(16px);
                }

                .toggle-label {
                    cursor: pointer;
                }

                .pulse-dot {
                    width: 8px;
                    height: 8px;
                    background-color: var(--primary-color, #0969da);
                    border-radius: 50%;
                    display: inline-block;
                    margin-right: 8px;
                    animation: pulse 2s infinite;
                }

                .user-query {
                    background: linear-gradient(
                        135deg,
                        var(--user-bg, #0969da),
                        var(--secondary-color, #0969da)
                    );
                    color: var(--user-text, white);
                    border-radius: 12px;
                    padding: 12px;
                    font-size: 14px;
                    line-height: 1.5;
                    max-height: 120px;
                    overflow-y: auto;
                    white-space: pre-wrap;
                    box-shadow: 0 4px 12px
                        rgba(var(--primary-rgb, 9, 105, 218), 0.2);
                    border: 1px solid rgba(var(--primary-rgb, 9, 105, 218), 0.3);
                }

                .animate-in {
                    animation: slideUpFade 0.5s cubic-bezier(0.16, 1, 0.3, 1);
                }

                .textarea-wrapper {
                    position: relative;
                    transition: all 0.3s ease;
                    border-radius: 12px;
                }

                .textarea-wrapper.has-changed {
                    box-shadow: 0 0 0 2px
                        rgba(var(--primary-rgb, 9, 105, 218), 0.2);
                    animation: glow 2s infinite;
                }

                .change-indicator {
                    position: absolute;
                    top: -10px;
                    right: 10px;
                    z-index: 1;
                }

                .change-badge {
                    background: linear-gradient(135deg, #ff6b6b, #ffa502);
                    color: white;
                    padding: 3px 10px;
                    border-radius: 20px;
                    font-size: 12px;
                    font-weight: bold;
                    box-shadow: 0 2px 5px rgba(0, 0, 0, 0.2);
                    animation: bounce 1s infinite;
                }

                .edit-instructions {
                    font-size: 13px;
                    color: var(--text-secondary, #6e7781);
                    font-style: italic;
                    margin-top: 8px;
                    display: flex;
                    align-items: center;
                    gap: 6px;
                }

                .tip-icon {
                    animation: float 3s ease-in-out infinite;
                    display: inline-block;
                }

                .suggest-edit-input textarea {
                    width: 100%;
                    padding: 12px;
                    border: 1px solid var(--border-color, #e1e4e8);
                    border-radius: 12px;
                    resize: none;
                    font-size: 14px;
                    line-height: 1.5;
                    background-color: var(--input-bg, #ffffff);
                    color: var(--text-color, #24292f);
                    transition: all 0.3s;
                    font-family: inherit;
                    min-height: 180px;
                    box-shadow: inset 0 1px 3px rgba(0, 0, 0, 0.05);
                }

                .suggest-edit-input textarea:focus {
                    outline: none;
                    border-color: var(--primary-color, #0969da);
                    box-shadow: 0 0 0 3px
                            rgba(var(--primary-rgb, 9, 105, 218), 0.2),
                        inset 0 1px 3px rgba(0, 0, 0, 0.05);
                }

                .highlight-changes {
                    background: linear-gradient(
                        to right,
                        transparent 0%,
                        transparent 100%
                    ) !important;
                    position: relative;
                }

                .suggest-edit-actions {
                    display: flex;
                    justify-content: flex-end;
                    padding: 12px 20px;
                    border-top: 1px solid var(--border-color, #e1e4e8);
                    gap: 16px;
                    background: linear-gradient(
                        to right,
                        rgba(var(--primary-rgb, 9, 105, 218), 0.02),
                        var(--container-bg, #ffffff)
                    );
                }

                .suggest-edit-cancel,
                .suggest-edit-submit {
                    padding: 10px 20px;
                    border-radius: 8px;
                    font-size: 14px;
                    font-weight: 500;
                    cursor: pointer;
                    transition: all 0.2s;
                    position: relative;
                    overflow: hidden;
                }

                .suggest-edit-cancel {
                    background-color: var(--hover-color, #f6f8fa);
                    border: 1px solid var(--border-color, #e1e4e8);
                    color: var(--text-color, #24292f);
                }

                .suggest-edit-cancel:hover {
                    background-color: var(--hover-color-light, #ebecf0);
                    transform: translateY(-2px);
                    box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
                }

                .suggest-edit-submit {
                    background: linear-gradient(
                        135deg,
                        var(--primary-color, #0969da),
                        var(--secondary-color, #0969da)
                    );
                    border: none;
                    color: white;
                    padding: 10px 24px;
                    display: flex;
                    align-items: center;
                    gap: 8px;
                }

                .suggest-edit-submit:hover {
                    transform: translateY(-2px);
                    box-shadow: 0 4px 12px
                        rgba(var(--primary-rgb, 9, 105, 218), 0.3);
                }

                .suggest-edit-submit:active:not(:disabled) {
                    transform: translateY(1px);
                }

                .suggest-edit-submit:disabled {
                    opacity: 0.6;
                    cursor: not-allowed;
                    transform: none;
                    box-shadow: none;
                }

                .button-arrow {
                    opacity: 0;
                    transform: translateX(-5px);
                    transition: all 0.3s;
                }

                .suggest-edit-submit:not(:disabled) .button-arrow {
                    opacity: 1;
                    transform: translateX(0);
                }

                .suggest-edit-submit:hover:not(:disabled) .button-arrow {
                    animation: moveRightLeft 1s infinite;
                }

                .ripple {
                    position: absolute;
                    border-radius: 50%;
                    background-color: rgba(255, 255, 255, 0.4);
                    width: 100px;
                    height: 100px;
                    transform: scale(0);
                    animation: ripple 0.6s linear;
                    top: calc(50% - 50px);
                    left: calc(50% - 50px);
                }

                @keyframes ripple {
                    to {
                        transform: scale(2.5);
                        opacity: 0;
                    }
                }

                @keyframes fadeIn {
                    from {
                        opacity: 0;
                    }
                    to {
                        opacity: 1;
                    }
                }

                @keyframes fadeOut {
                    from {
                        opacity: 1;
                    }
                    to {
                        opacity: 0;
                    }
                }

                @keyframes slideIn {
                    from {
                        transform: translateY(20px) scale(0.96);
                        opacity: 0;
                    }
                    to {
                        transform: translateY(0) scale(1);
                        opacity: 1;
                    }
                }

                @keyframes slideOut {
                    from {
                        transform: translateY(0) scale(1);
                        opacity: 1;
                    }
                    to {
                        transform: translateY(20px) scale(0.96);
                        opacity: 0;
                    }
                }

                @keyframes slideUpFade {
                    from {
                        transform: translateY(10px);
                        opacity: 0;
                    }
                    to {
                        transform: translateY(0);
                        opacity: 1;
                    }
                }

                @keyframes pulse {
                    0% {
                        box-shadow: 0 0 0 0
                            rgba(var(--primary-rgb, 9, 105, 218), 0.4);
                    }
                    70% {
                        box-shadow: 0 0 0 6px
                            rgba(var(--primary-rgb, 9, 105, 218), 0);
                    }
                    100% {
                        box-shadow: 0 0 0 0
                            rgba(var(--primary-rgb, 9, 105, 218), 0);
                    }
                }

                @keyframes pulseScale {
                    0% {
                        transform: scale(1);
                    }
                    50% {
                        transform: scale(1.1);
                    }
                    100% {
                        transform: scale(1);
                    }
                }

                @keyframes float {
                    0% {
                        transform: translateY(0px);
                    }
                    50% {
                        transform: translateY(-5px);
                    }
                    100% {
                        transform: translateY(0px);
                    }
                }

                @keyframes bounce {
                    0%,
                    100% {
                        transform: translateY(0);
                    }
                    50% {
                        transform: translateY(-3px);
                    }
                }

                @keyframes glow {
                    0%,
                    100% {
                        box-shadow: 0 0 0 2px
                            rgba(var(--primary-rgb, 9, 105, 218), 0.2);
                    }
                    50% {
                        box-shadow: 0 0 0 2px
                            rgba(var(--primary-rgb, 9, 105, 218), 0.4);
                    }
                }

                @keyframes moveRightLeft {
                    0%,
                    100% {
                        transform: translateX(0);
                    }
                    50% {
                        transform: translateX(3px);
                    }
                }

                @keyframes rotate {
                    from {
                        transform: rotate(0deg);
                    }
                    to {
                        transform: rotate(360deg);
                    }
                }
            `}</style>
        </div>
    );
};

export default SuggestEditModal;
