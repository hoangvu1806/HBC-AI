import React, { useEffect, useState } from 'react';
import styles from '@/styles/Chat.module.css';
import { ID_HBC_LOGIN_URL } from '@/lib/api';
import { FiAlertCircle } from 'react-icons/fi';

const SessionExpiredModal: React.FC = () => {
    const [isVisible, setIsVisible] = useState(true);
    const [isClosing, setIsClosing] = useState(false);

    useEffect(() => {
        // Khi component được mount, thêm class để ngăn scroll trên body
        document.body.style.overflow = 'hidden';
        
        // Khi component unmount, restore lại scroll
        return () => {
            document.body.style.overflow = 'auto';
        };
    }, []);

    const handleLogin = () => {
        // Thêm trạng thái đóng có animation
        setIsClosing(true);
        setTimeout(() => {
            // Chuyển hướng đến trang đăng nhập HBC
            window.location.href = `${ID_HBC_LOGIN_URL}?app_redirect_url=${btoa(
                window.location.href
            )}`;
        }, 300);
    };

    if (!isVisible) return null;

    return (
        <div className={`${styles.modalOverlay} ${isClosing ? styles.closing : ''}`}>
            <div className={`${styles.modalContainer} ${isClosing ? styles.closing : ''}`}>
                <div className={styles.modalHeader}>
                    <h3><FiAlertCircle className={styles.modalIcon} /> Phiên làm việc hết hạn</h3>
                </div>
                <div className={styles.modalContent}>
                    <p>Phiên làm việc của bạn đã hết hạn. Vui lòng đăng nhập lại để tiếp tục sử dụng hệ thống.</p>
                </div>
                <div className={styles.modalFooter}>
                    <button className={styles.primaryButton} onClick={handleLogin}>
                        Đăng nhập lại
                    </button>
                </div>
            </div>
        </div>
    );
};

export default SessionExpiredModal; 