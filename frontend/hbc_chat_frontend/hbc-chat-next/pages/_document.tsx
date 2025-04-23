import { Html, Head, Main, NextScript } from "next/document";

export default function Document() {
    return (
        <Html lang="vi" style={{ height: "100%" }}>
            <Head>
                <link
                    rel="stylesheet"
                    href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css"
                />
                <link
                    rel="stylesheet"
                    href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.7.0/styles/github.min.css"
                />
                <link
                    rel="stylesheet"
                    href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap"
                />
            </Head>
            <body style={{ height: "100%", margin: 0, padding: 0 }}>
                <Main />
                <NextScript />
            </body>
        </Html>
    );
}
