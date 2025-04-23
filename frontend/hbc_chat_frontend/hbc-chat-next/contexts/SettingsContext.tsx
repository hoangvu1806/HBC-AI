import {
    createContext,
    useContext,
    useState,
    useEffect,
    ReactNode,
} from "react";

interface SettingsType {
    darkMode: boolean;
    fontSize: "small" | "medium" | "large";
    aiTopic: string;
}

interface SettingsContextType {
    settings: SettingsType;
    updateSettings: (key: keyof SettingsType, value: any) => void;
}

const defaultSettings: SettingsType = {
    darkMode: false,
    fontSize: "medium",
    aiTopic: "HCNS",
};

const SettingsContext = createContext<SettingsContextType | undefined>(
    undefined
);

export const SettingsProvider = ({ children }: { children: ReactNode }) => {
    const [settings, setSettings] = useState<SettingsType>(defaultSettings);

    // Load settings from localStorage on initial render
    useEffect(() => {
        const storedSettings = localStorage.getItem("hbc-chat-settings");
        if (storedSettings) {
            try {
                const parsedSettings = JSON.parse(storedSettings);
                setSettings(parsedSettings);
            } catch (error) {
                console.error(
                    "Failed to parse settings from localStorage",
                    error
                );
            }
        }
    }, []);

    // Apply dark mode class to body
    useEffect(() => {
        if (settings.darkMode) {
            document.body.classList.add("dark-mode");
        } else {
            document.body.classList.remove("dark-mode");
        }
    }, [settings.darkMode]);

    // Apply font size
    useEffect(() => {
        document.documentElement.style.setProperty(
            "--font-size-base",
            settings.fontSize === "small"
                ? "14px"
                : settings.fontSize === "large"
                ? "18px"
                : "16px"
        );
    }, [settings.fontSize]);

    const updateSettings = (key: keyof SettingsType, value: any) => {
        const newSettings = { ...settings, [key]: value };
        setSettings(newSettings);

        // Save to localStorage
        localStorage.setItem("hbc-chat-settings", JSON.stringify(newSettings));
    };

    return (
        <SettingsContext.Provider value={{ settings, updateSettings }}>
            {children}
        </SettingsContext.Provider>
    );
};

export const useSettings = () => {
    const context = useContext(SettingsContext);
    if (context === undefined) {
        throw new Error("useSettings must be used within a SettingsProvider");
    }
    return context;
};
