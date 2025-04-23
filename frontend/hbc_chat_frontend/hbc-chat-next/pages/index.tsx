import Head from "next/head";
import ChatArea from "@/components/chat/ChatArea";

export default function Home() {
    return (
        <>
            <Head>
                <title>HBC AI Assistant</title>
                <meta
                    name="description"
                    content="HBC AI Assistant - Chatbot thông minh hỗ trợ các vấn đề của HBC"
                />
                <meta
                    name="viewport"
                    content="width=device-width, initial-scale=1"
                />
                <link rel="icon" href="/logo-HBC.png" />
            </Head>

            <ChatArea />
        </>
    );
}
