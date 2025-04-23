import "@/styles/globals.css";
import type { AppProps } from "next/app";
import { SettingsProvider } from "@/contexts/SettingsContext";
import { ChatProvider } from "@/contexts/ChatContext";
import Layout from "@/components/layout/Layout";

export default function App({ Component, pageProps }: AppProps) {
    return (
        <SettingsProvider>
            <ChatProvider>
                <Layout>
                    <Component {...pageProps} />
                </Layout>
            </ChatProvider>
        </SettingsProvider>
    );
}
