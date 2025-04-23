import {
    FaBriefcase,
    FaCalendarAlt,
    FaUserTie,
    FaFileAlt,
} from "react-icons/fa";
import styles from "@/styles/Chat.module.css";

interface ChatWelcomeProps {
    onSuggestionClick: (suggestion: string) => void;
}

const ChatWelcome = ({ onSuggestionClick }: ChatWelcomeProps) => {
    return (
        <div className={styles.chatWelcome}>
            <h1>HBC AI Assistant</h1>

            <div className={styles.welcomeSuggestions}>
                <div className={styles.suggestionRow}>
                    <div
                        className={styles.suggestionCard}
                        onClick={() =>
                            onSuggestionClick("Thủ tục xin nghỉ phép")
                        }
                    >
                        <div className={styles.suggestionTitle}>
                            <FaCalendarAlt /> Nghỉ phép
                        </div>
                        <div className={styles.suggestionExamples}>
                            <p>&quot;Thủ tục xin nghỉ phép&quot;</p>
                            <p>&quot;Quy định về nghỉ phép năm&quot;</p>
                        </div>
                    </div>

                    <div
                        className={styles.suggestionCard}
                        onClick={() =>
                            onSuggestionClick("Quy trình đánh giá nhân viên")
                        }
                    >
                        <div className={styles.suggestionTitle}>
                            <FaUserTie /> Nhân sự
                        </div>
                        <div className={styles.suggestionExamples}>
                            <p>&quot;Quy trình đánh giá nhân viên&quot;</p>
                            <p>&quot;Chính sách phát triển nhân viên&quot;</p>
                        </div>
                    </div>
                </div>

                <div className={styles.suggestionRow}>
                    <div
                        className={styles.suggestionCard}
                        onClick={() =>
                            onSuggestionClick("Chính sách phúc lợi công ty")
                        }
                    >
                        <div className={styles.suggestionTitle}>
                            <FaBriefcase /> Phúc lợi
                        </div>
                        <div className={styles.suggestionExamples}>
                            <p>&quot;Chính sách phúc lợi công ty&quot;</p>
                            <p>&quot;Quy định về bảo hiểm nhân viên&quot;</p>
                        </div>
                    </div>

                    <div
                        className={styles.suggestionCard}
                        onClick={() =>
                            onSuggestionClick("Thủ tục thanh toán chi phí")
                        }
                    >
                        <div className={styles.suggestionTitle}>
                            <FaFileAlt /> Hành chính
                        </div>
                        <div className={styles.suggestionExamples}>
                            <p>&quot;Thủ tục thanh toán chi phí&quot;</p>
                            <p>&quot;Quy trình cấp phát văn phòng phẩm&quot;</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default ChatWelcome;
