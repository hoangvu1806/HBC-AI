import { useRef, useEffect } from "react";
import { useChat } from "@/contexts/ChatContext";
import { useSettings } from "@/contexts/SettingsContext";
import ChatWelcome from "./ChatWelcome";
import ChatInput from "./ChatInput";
import Message from "./Message";
import styles from "@/styles/Chat.module.css";

const ChatArea = () => {
    const {
        messages,
        sendMessage,
        isThinkModeActive,
        toggleThinkMode,
        rateMessage,
        isWaitingResponse,
    } = useChat();

    const { settings } = useSettings();
    const messagesEndRef = useRef<HTMLDivElement>(null);

    // Scroll to bottom when messages change or when waiting state changes
    useEffect(() => {
        if (messagesEndRef.current) {
            const scrollBehavior = isWaitingResponse ? "auto" : "smooth";
            messagesEndRef.current.scrollIntoView({ behavior: scrollBehavior });
        }
    }, [messages, isWaitingResponse]);

    const handleSendMessage = (content: string) => {
        sendMessage(content);
    };

    const handleSuggestionClick = (suggestion: string) => {
        sendMessage(suggestion);
    };

    const handleRateMessage = (messageId: string, rating: number) => {
        rateMessage(messageId, rating);
    };

    return (
        <div className={styles.chatContainer}>
            <div className={styles.chatMessages}>
                {messages.length === 0 ? (
                    <ChatWelcome onSuggestionClick={handleSuggestionClick} />
                ) : (
                    messages.map((message) => (
                        <Message
                            key={message.id}
                            id={message.id}
                            content={message.content}
                            isUser={message.isUser}
                            timestamp={message.timestamp}
                            hasFiles={message.hasFiles}
                            showRating={
                                !message.isUser &&
                                settings.showRatings &&
                                !message.rating
                            }
                            onRate={(rating) =>
                                handleRateMessage(message.id, rating)
                            }
                        />
                    ))
                )}
                <div ref={messagesEndRef} />
            </div>

            <ChatInput
                onSendMessage={handleSendMessage}
                isThinkModeActive={isThinkModeActive}
                toggleThinkMode={toggleThinkMode}
                isWaitingResponse={isWaitingResponse}
            />
        </div>
    );
};

export default ChatArea;
