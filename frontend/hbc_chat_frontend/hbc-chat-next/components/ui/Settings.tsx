import { 
    FaTimes, 
    FaMoon, 
    FaDownload, 
    FaTrashAlt, 
    FaUserTie 
} from "react-icons/fa";
import { 
    FiMonitor, 
    FiSettings, 
    FiClock 
} from "react-icons/fi";
import styles from "@/styles/Settings.module.css";
import { useState } from "react";
import ConfirmDialog from "./ConfirmDialog";

interface SettingsProps {
    isOpen: boolean;
    closeSettings: () => void;
    settings: {
        darkMode: boolean;
        fontSize: "small" | "medium" | "large";
        aiTopic: string;
    };
    updateSettings: (key: string, value: any) => void;
    exportChat: () => void;
    clearHistory: () => void;
}

const Settings = ({
    isOpen,
    closeSettings,
    settings,
    updateSettings,
    exportChat,
    clearHistory,
}: SettingsProps) => {
    const [showConfirmClear, setShowConfirmClear] = useState(false);

    const handleDarkModeChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        updateSettings("darkMode", e.target.checked);
        document.body.classList.toggle("dark-mode", e.target.checked);
    };

    const handleClearHistory = () => {
        setShowConfirmClear(true);
    };

    const confirmClearHistory = () => {
        clearHistory();
        setShowConfirmClear(false);
    };

    const cancelClearHistory = () => {
        setShowConfirmClear(false);
    };

    return (
        <>
            <div
                className={`${styles.settingsPanel} ${
                    isOpen ? styles.active : ""
                }`}
            >
                <div className={styles.settingsHeader}>
                    <h3>Cài đặt</h3>
                    <button onClick={closeSettings} title="Đóng cài đặt">
                        <FaTimes />
                    </button>
                </div>

                <div className={styles.settingsContent}>
                    <div className={styles.settingGroup}>
                        <h4>
                            <FiMonitor /> Hiển thị
                        </h4>

                        <div className={styles.settingItem}>
                            <span>
                                <FaMoon /> Chế độ tối
                            </span>
                            <label className={styles.switch}>
                                <input
                                    type="checkbox"
                                    checked={settings.darkMode}
                                    onChange={handleDarkModeChange}
                                />
                                <span
                                    className={`${styles.slider} ${styles.round}`}
                                ></span>
                            </label>
                        </div>
                    </div>

                    <div className={styles.settingGroup}>
                        <h4>
                            <FiSettings /> Tùy chọn bot
                        </h4>

                        <div className={styles.settingItem}>
                            <span>
                                <FaUserTie /> Chuyên viên AI
                            </span>
                            <select
                                className={styles.select}
                                value={settings.aiTopic}
                                onChange={(e) =>
                                    updateSettings("aiTopic", e.target.value)
                                }
                            >
                                <option value="HCNS">HCNS</option>
                                <option value="IT">IT</option>
                                <option value="KT">Kế toán</option>
                                <option value="KINH_DOANH">Kinh doanh</option>
                                <option value="TGD">Ban TGĐ</option>
                            </select>
                        </div>
                    </div>

                    <div className={styles.settingGroup}>
                        <h4>
                            <FiClock /> Lịch sử
                        </h4>
                        <button
                            className={styles.btnSecondary}
                            onClick={exportChat}
                        >
                            <FaDownload /> Xuất lịch sử trò chuyện
                        </button>
                        <button
                            className={styles.btnDanger}
                            onClick={handleClearHistory}
                        >
                            <FaTrashAlt /> Xóa lịch sử
                        </button>
                    </div>
                </div>
            </div>

            <ConfirmDialog
                isOpen={showConfirmClear}
                title="Xóa toàn bộ lịch sử"
                message="Bạn có chắc chắn muốn xóa toàn bộ lịch sử trò chuyện không? Hành động này sẽ xóa tất cả các cuộc trò chuyện và không thể hoàn tác."
                confirmText="Xóa tất cả"
                cancelText="Hủy"
                onConfirm={confirmClearHistory}
                onCancel={cancelClearHistory}
                type="danger"
            />
        </>
    );
};

export default Settings;
