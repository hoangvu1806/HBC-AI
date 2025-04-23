import React, { useEffect, useRef } from "react";
import { IoMdClose } from "react-icons/io";
import { FiAlertTriangle } from "react-icons/fi";

interface ConfirmDialogProps {
    isOpen: boolean;
    title: string;
    message: string;
    confirmText?: string;
    cancelText?: string;
    onConfirm: () => void;
    onCancel: () => void;
    type?: "danger" | "warning" | "info";
}

const ConfirmDialog: React.FC<ConfirmDialogProps> = ({
    isOpen,
    title,
    message,
    confirmText = "Xác nhận",
    cancelText = "Hủy",
    onConfirm,
    onCancel,
    type = "danger",
}) => {
    const dialogRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        const handleClickOutside = (event: MouseEvent) => {
            if (
                dialogRef.current &&
                !dialogRef.current.contains(event.target as Node)
            ) {
                onCancel();
            }
        };

        const handleEscKey = (event: KeyboardEvent) => {
            if (event.key === "Escape") {
                onCancel();
            }
        };

        if (isOpen) {
            document.addEventListener("mousedown", handleClickOutside);
            document.addEventListener("keydown", handleEscKey);
        }

        return () => {
            document.removeEventListener("mousedown", handleClickOutside);
            document.removeEventListener("keydown", handleEscKey);
        };
    }, [isOpen, onCancel]);

    if (!isOpen) return null;

    return (
        <div className="confirm-dialog-overlay">
            <div className="confirm-dialog" ref={dialogRef}>
                <div className="confirm-dialog-header">
                    <div className="confirm-dialog-title">
                        {type === "danger" && (
                            <FiAlertTriangle className="confirm-dialog-icon" />
                        )}
                        {title}
                    </div>
                    <button className="confirm-dialog-close" onClick={onCancel}>
                        <IoMdClose />
                    </button>
                </div>
                <div className="confirm-dialog-content">{message}</div>
                <div className="confirm-dialog-actions">
                    <button
                        className="confirm-dialog-cancel"
                        onClick={onCancel}
                    >
                        {cancelText}
                    </button>
                    <button
                        className={`confirm-dialog-confirm ${
                            type === "danger" ? "confirm-dialog-danger" : ""
                        }`}
                        onClick={onConfirm}
                    >
                        {confirmText}
                    </button>
                </div>
            </div>
            <style jsx>{`
                .confirm-dialog-overlay {
                    position: fixed;
                    top: 0;
                    left: 0;
                    right: 0;
                    bottom: 0;
                    background-color: rgba(0, 0, 0, 0.5);
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    z-index: 9999;
                    animation: fadeIn 0.2s;
                }

                .confirm-dialog {
                    background-color: #fff;
                    border-radius: 8px;
                    width: 400px;
                    max-width: 90vw;
                    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
                    animation: slideIn 0.2s;
                }

                :global(.dark-mode) .confirm-dialog {
                    background-color: #2d333b;
                    color: #e6edf3;
                }

                .confirm-dialog-header {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    padding: 16px 20px;
                    border-bottom: 1px solid #e1e4e8;
                }

                :global(.dark-mode) .confirm-dialog-header {
                    border-color: #444c56;
                }

                .confirm-dialog-title {
                    font-weight: 600;
                    font-size: 16px;
                    display: flex;
                    align-items: center;
                    gap: 8px;
                }

                .confirm-dialog-icon {
                    color: #d73a49;
                    font-size: 18px;
                }

                .confirm-dialog-close {
                    background: none;
                    border: none;
                    color: #6e7781;
                    cursor: pointer;
                    font-size: 20px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    padding: 4px;
                    border-radius: 4px;
                }

                .confirm-dialog-close:hover {
                    background-color: #f6f8fa;
                    color: #24292f;
                }

                :global(.dark-mode) .confirm-dialog-close:hover {
                    background-color: #373e47;
                    color: #e6edf3;
                }

                .confirm-dialog-content {
                    padding: 20px;
                    line-height: 1.5;
                }

                .confirm-dialog-actions {
                    display: flex;
                    justify-content: flex-end;
                    padding: 12px 20px 20px;
                    gap: 12px;
                }

                .confirm-dialog-cancel,
                .confirm-dialog-confirm {
                    padding: 8px 16px;
                    border-radius: 6px;
                    font-size: 14px;
                    font-weight: 500;
                    cursor: pointer;
                    transition: all 0.2s;
                }

                .confirm-dialog-cancel {
                    background-color: #f6f8fa;
                    border: 1px solid rgba(27, 31, 36, 0.15);
                    color: #24292f;
                }

                :global(.dark-mode) .confirm-dialog-cancel {
                    background-color: #373e47;
                    border-color: #444c56;
                    color: #e6edf3;
                }

                .confirm-dialog-cancel:hover {
                    background-color: #f3f4f6;
                }

                :global(.dark-mode) .confirm-dialog-cancel:hover {
                    background-color: #444c56;
                }

                .confirm-dialog-confirm {
                    background-color: #2da44e;
                    border: 1px solid rgba(27, 31, 36, 0.15);
                    color: #ffffff;
                }

                .confirm-dialog-confirm:hover {
                    background-color: #2c974b;
                }

                .confirm-dialog-danger {
                    background-color: #d73a49;
                }

                .confirm-dialog-danger:hover {
                    background-color: #cb2431;
                }

                @keyframes fadeIn {
                    from {
                        opacity: 0;
                    }
                    to {
                        opacity: 1;
                    }
                }

                @keyframes slideIn {
                    from {
                        transform: translateY(-20px);
                        opacity: 0;
                    }
                    to {
                        transform: translateY(0);
                        opacity: 1;
                    }
                }
            `}</style>
        </div>
    );
};

export default ConfirmDialog;
