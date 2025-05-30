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
                        />
                    ))
                )}
                <div ref={messagesEndRef} style={{ paddingBottom: "8px" }} />
            </div>

            <ChatInput
                onSendMessage={handleSendMessage}
                isThinkModeActive={isThinkModeActive}
                toggleThinkMode={toggleThinkMode}
                isWaitingResponse={isWaitingResponse}
                aiTopic={settings.aiTopic}
            />
        </div>
    );
};

export default ChatArea;
