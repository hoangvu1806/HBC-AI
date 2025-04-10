document.addEventListener("DOMContentLoaded", function () {
    // Khai báo biến để theo dõi trạng thái tải CryptoJS
    let cryptoJSLoaded = typeof CryptoJS !== "undefined";
    let pendingDataCallbacks = [];

    // Tải CryptoJS nếu chưa có
    if (!cryptoJSLoaded) {
        const cryptoScript = document.createElement("script");
        cryptoScript.src =
            "https://cdnjs.cloudflare.com/ajax/libs/crypto-js/4.1.1/crypto-js.min.js";
        cryptoScript.integrity =
            "sha512-E8QSvWZ0eCLGk4km3hxSsNmGWbLtSCSUcewDQPQWZF6pEU8GlT8a5fF32wOl1i8ftdMhssTrF/OhyGWwonTcXA==";
        cryptoScript.crossOrigin = "anonymous";
        cryptoScript.referrerPolicy = "no-referrer";

        // Đợi script tải xong
        cryptoScript.onload = function () {
            console.log("CryptoJS đã tải xong");
            cryptoJSLoaded = true;

            // Xử lý các callback đang chờ
            for (let callback of pendingDataCallbacks) {
                processDataCallback(callback);
            }
            pendingDataCallbacks = [];
        };

        document.head.appendChild(cryptoScript);
    }

    // Khai báo các biến và elements
    const chatMessages = document.getElementById("chat-messages");
    const userInput = document.getElementById("user-input");
    const sendBtn = document.getElementById("send-btn");
    const themeToggle = document.getElementById("theme-toggle");
    const clearChatBtn = document.getElementById("clear-chat");
    const settingsBtn = document.getElementById("settings-btn");
    const closeSettingsBtn = document.getElementById("close-settings");
    const settingsPanel = document.getElementById("settings-panel");
    const darkModeToggle = document.getElementById("dark-mode-toggle");
    const fontSizeSelect = document.getElementById("font-size");
    const exportChatBtn = document.getElementById("export-chat");
    const clearHistoryBtn = document.getElementById("clear-history");
    const uploadBtn = document.getElementById("upload-btn");
    const ratingToggle = document.getElementById("rating-toggle");
    const thinkToggleBtn = document.getElementById("think-toggle-btn");

    // Các phần tử mới trong giao diện ChatGPT style
    const toggleSidebarBtn = document.getElementById("toggle-sidebar");
    const sidebar = document.querySelector(".sidebar");
    const userAvatar = document.getElementById("user-avatar");
    const userDropdown = document.getElementById("user-dropdown");
    const logoutBtn = document.getElementById("logout-btn");
    const newChatBtn = document.getElementById("new-chat-btn");

    const suggestionCards = document.querySelectorAll(".suggestion-card");
    const chatWelcome = document.querySelector(".chat-welcome");

    // Thêm biến kiểm soát tính năng đánh giá
    let showRatings = localStorage.getItem("showRatings") === "true";

    // Thêm biến kiểm soát chế độ Think
    let thinkEnabled = localStorage.getItem("thinkEnabled") === "true";

    // Khai báo biến lưu đánh giá
    let messageRatings = {};

    // Thêm biến toàn cục để theo dõi ID chat hiện tại
    let currentChatId = null;
    let chats = {};

    // Biến môi trường cho URL đăng nhập HBC
    const ID_HBC_LOGIN_URL = "https://id-staging.hbc.com.vn";

    // Khóa AES để giải mã dữ liệu từ ID HBC
    const GOOGLE_AES_KEY = "u2a0d40mf4b6t06s51oqkd20lqh132dq";

    // Hàm kiểm tra access token
    async function checkAccessToken() {
        try {
            let accessToken = getCookie("access_token");
            let hostUrl = window.location.origin;
            const apiUrl = `https://id-api-staging.hbc.com.vn/v1/user/auth/google/access-token?accessToken=${encodeURIComponent(
                accessToken
            )}`;
            // Sử dụng endpoint từ biến API_ENDPOINTS
            const response = await fetch(apiUrl, {
                method: "GET",
                headers: {
                    "Content-Type": "application/json",
                },
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(
                    errorData.message || "Không thể xác thực token"
                );
            }

            return await response.json();
        } catch (error) {
            console.error("Lỗi kiểm tra token:", error);
            throw error;
        }
    }

    // Hàm lấy cookie
    function getCookie(name) {
        const value = `; ${document.cookie}`;
        const parts = value.split(`; ${name}=`);
        if (parts.length === 2) return parts.pop().split(";").shift();
        return null;
    }

    // Hàm thiết lập cookie
    function setCookie(name, value, options = {}) {
        let expires = options.expires
            ? `; expires=${options.expires.toUTCString()}`
            : "";
        let path = options.path ? `; path=${options.path}` : "";
        document.cookie = `${name}=${value}${expires}${path}`;
    }

    // Hàm kiểm tra trạng thái đăng nhập khi tải trang
    async function checkAuth() {
        try {
            // Đặt timeout để tránh màn hình loading bị kẹt
            const authTimeout = setTimeout(() => {
                console.log("Quá thời gian xác thực, ẩn màn hình loading");
                hideLoadingScreen();
                alert("Quá thời gian xác thực. Vui lòng thử lại.");
            }, 15000); // 15 giây timeout

            // Kiểm tra xem có access_token hoặc refresh_token trong cookie không
            let isToken =
                getCookie("access_token") || getCookie("refresh_token");

            // Kiểm tra xem có dữ liệu callback từ ID HBC trong URL không
            const urlParams = new URLSearchParams(window.location.search);
            let isData = urlParams.get("data");

            if (isData) {
                showLoadingScreen("Đang xử lý dữ liệu đăng nhập...");
                await handleDataCallback(isData);

                // Xóa tham số data khỏi URL
                const newUrl = window.location.pathname + window.location.hash;
                window.history.replaceState({}, document.title, newUrl);

                clearTimeout(authTimeout); // Xóa timeout khi xử lý thành công

                setTimeout(() => {
                    hideLoadingScreen();
                }, 2000);
                return;
            }

            if (isToken) {
                showLoadingScreen("Đang kiểm tra thông tin đăng nhập...");
                await checkAccessToken();

                // Xóa timeout khi xử lý thành công
                clearTimeout(authTimeout);

                // Khôi phục thông tin người dùng từ localStorage
                restoreUserInfo();

                setTimeout(() => {
                    hideLoadingScreen();
                }, 2000);
            } else {
                // Xóa timeout vì sẽ chuyển hướng
                clearTimeout(authTimeout);

                // Ẩn loading trước khi chuyển hướng
                hideLoadingScreen();

                // Chuyển hướng đến trang đăng nhập ID HBC
                console.log("Không có token, chuyển hướng đến trang đăng nhập");
                window.location.href = `${ID_HBC_LOGIN_URL}?app_redirect_url=${btoa(
                    window.location.href
                )}`;
            }
        } catch (err) {
            console.error("Lỗi trong quá trình xác thực:", err);
            hideLoadingScreen();

            // Hiển thị thông báo lỗi chi tiết
            alert(
                "Lỗi trong quá trình xác thực: " +
                    (err.message || "Không xác định")
            );

            // Nếu có URL chuyển hướng trong phản hồi lỗi, thực hiện chuyển hướng
            if (err?.response?.data?.redirectUrl) {
                window.location.href = err.response.data.redirectUrl;
            }
        }
    }
    // Hàm khôi phục thông tin người dùng từ localStorage
    function restoreUserInfo() {
        try {
            const userData = localStorage.getItem("user");
            if (userData) {
                const user = JSON.parse(userData);
                updateUserInfo(user);
            }
        } catch (error) {
            console.error("Lỗi khi khôi phục thông tin người dùng:", error);
        }
    }

    // Hàm xử lý dữ liệu callback từ ID HBC
    async function handleDataCallback(data) {
        if (cryptoJSLoaded) {
            // Nếu CryptoJS đã tải xong, xử lý ngay
            processDataCallback(data);
        } else {
            // Nếu chưa tải xong, thêm vào queue để xử lý sau
            console.log("CryptoJS chưa tải xong. Đang thêm vào hàng đợi...");
            pendingDataCallbacks.push(data);
        }
    }

    // Hàm thực hiện xử lý dữ liệu callback
    function processDataCallback(data) {
        try {
            // Giải mã dữ liệu base64
            let dataDecodeBase64 = atob(data);

            if (typeof CryptoJS === "undefined") {
                throw new Error(
                    "CryptoJS chưa được tải. Vui lòng làm mới trang và thử lại."
                );
            }

            // Giải mã AES với khóa đã cung cấp
            const decryptedData = CryptoJS.AES.decrypt(
                dataDecodeBase64,
                GOOGLE_AES_KEY
            ).toString(CryptoJS.enc.Utf8);

            // Kiểm tra dữ liệu sau khi giải mã
            if (!decryptedData) {
                throw new Error(
                    "Không thể giải mã dữ liệu. Vui lòng kiểm tra khóa GOOGLE_AES_KEY."
                );
            }

            // Parse dữ liệu đăng nhập đã giải mã
            let dataLogin = JSON.parse(decryptedData);

            // Kiểm tra nếu user là false hoặc không tồn tại
            if (!dataLogin.user || dataLogin.user === false) {
                alert("Tài khoản chưa có quyền truy cập vào hệ thống.");
                // Điều hướng trở lại trang đăng nhập
                window.location.href = `${ID_HBC_LOGIN_URL}?app_redirect_url=${btoa(
                    window.location.href
                )}`;
                return;
            }

            // Lưu thông tin người dùng vào localStorage hoặc biến toàn cục
            localStorage.setItem("user", JSON.stringify(dataLogin.user));

            // Lưu token vào cookie
            setCookie("access_token", dataLogin.access_token, {
                path: "/",
                expires: new Date(Number(dataLogin.user.exp) * 1000),
            });
            setCookie("refresh_token", dataLogin.refresh_token, { path: "/" });

            // Cập nhật giao diện người dùng
            updateUserInfo(dataLogin.user);
        } catch (err) {
            console.error("Lỗi xử lý dữ liệu callback:", err);
            alert(`Lỗi xử lý dữ liệu đăng nhập: ${err.message}`);
        }
    }

    // Hàm cập nhật thông tin người dùng trong giao diện
    function updateUserInfo(user) {
        console.log("Cập nhật thông tin người dùng:", user);
        // Cập nhật thông tin người dùng trong phần user-info
        const userInfo = document.querySelector(".user-info");
        if (userInfo) {
            // Cập nhật tên và email
            const nameElement = userInfo.querySelector(".user-name");
            if (nameElement) {
                nameElement.textContent = user.displayName || "Người dùng";
            }

            const emailElement = userInfo.querySelector(".user-email");
            if (emailElement) {
                emailElement.textContent =
                    user.emailAddress || "user@example.com";
            }

            // Cập nhật avatar
            const avatarImg = userInfo.querySelector("img");
            if (avatarImg) {
                if (user.avatar) {
                    avatarImg.src = user.picture;
                    avatarImg.alt = `${
                        user.displayName || "Người dùng"
                    } Avatar`;
                } else {
                    avatarImg.src = user.picture;
                    avatarImg.alt = `${
                        user.displayName || "Người dùng"
                    } Avatar`;
                }
            }
        }

        // Cập nhật thông tin trong dropdown nếu có
        if (document.querySelector(".user-dropdown .user-name")) {
            document.querySelector(".user-dropdown .user-name").textContent =
                user.displayName || "Người dùng";
        }

        if (document.querySelector(".user-dropdown .user-email")) {
            document.querySelector(".user-dropdown .user-email").textContent =
                user.emailAddress || "user@example.com";
        }

        // Cập nhật tất cả các avatar khác trong trang
        const allAvatars = document.querySelectorAll(".user-avatar img");
        if (allAvatars.length > 0) {
            if (user.avatar) {
                allAvatars.forEach((img) => {
                    img.src = user.picture;
                    img.alt = `${user.displayName || "Người dùng"} Avatar`;
                });
            } else {
                allAvatars.forEach((img) => {
                    img.src = user.picture;
                    img.alt = `${user.displayName || "Người dùng"} Avatar`;
                });
            }
        }
    }

    // Hiển thị màn hình loading
    function showLoadingScreen(message = "Đang tải...") {
        // Xóa màn hình loading cũ nếu có
        hideLoadingScreen();

        const loadingScreen = document.createElement("div");
        loadingScreen.id = "loading-screen";
        loadingScreen.innerHTML = `
            <div class="loading-container">
                <div class="loading-spinner"></div>
                <p>${message}</p>
            </div>
        `;
        document.body.appendChild(loadingScreen);

        console.log("Hiển thị màn hình loading:", message);
    }

    // Ẩn màn hình loading
    function hideLoadingScreen() {
        const loadingScreen = document.getElementById("loading-screen");
        if (loadingScreen) {
            loadingScreen.remove();
            // console.log("Đã ẩn màn hình loading");
        }
    }

    // Thêm sự kiện đăng xuất
    if (logoutBtn) {
        logoutBtn.addEventListener("click", function (e) {
            e.preventDefault();
            // Xóa cookies và localStorage
            document.cookie =
                "access_token=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";
            document.cookie =
                "refresh_token=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";
            localStorage.removeItem("user");

            // Chuyển hướng đến trang đăng nhập
            window.location.href = `${ID_HBC_LOGIN_URL}?app_redirect_url=${btoa(
                window.location.href
            )}`;
        });
    }

    // Gọi hàm kiểm tra xác thực khi tải trang
    checkAuth();

    // Cấu hình Marked.js để render Markdown
    marked.setOptions({
        renderer: new marked.Renderer(),
        highlight: function (code, lang) {
            if (lang && hljs.getLanguage(lang)) {
                return hljs.highlight(code, { language: lang }).value;
            }
            return hljs.highlightAuto(code).value;
        },
        pedantic: false,
        gfm: true,
        breaks: true,
        sanitize: false,
        smartypants: false,
        xhtml: false,
    });

    // Cần phải cập nhật lại 'conversationItems' mỗi khi có thay đổi
    function updateConversationItemsReference() {
        return document.querySelectorAll(".conversation-item");
    }

    // Cập nhật lại biến conversationItems
    let conversationItems = updateConversationItemsReference();

    // Thêm biến lưu giá trị topic mặc định
    const defaultTopic = "HCNS";
    let currentTopic = localStorage.getItem("chatTopic") || defaultTopic;
    let uploadedFiles = [];

    // Thêm hàm gọi API
    async function callChatAPI(message, sectionName, files = []) {
        try {
            const apiUrl = "https://n8nai.hbc.com.vn/webhook/hcns";

            // Lấy thông tin người dùng từ localStorage
            const userData = localStorage.getItem("user");
            let userEmail = "guest";
            if (userData) {
                const user = JSON.parse(userData);
                userEmail = user.emailAddress || "guest";
            }

            // Chuẩn bị dữ liệu gửi đi
            const formData = new FormData();
            formData.append("topic", currentTopic);
            formData.append("user_email", userEmail);
            formData.append("prompt", message);
            formData.append("section_name", sectionName);
            formData.append("mode", thinkEnabled ? "think" : "normal");
            // Thêm files nếu có
            if (files && files.length > 0) {
                files.forEach((file, index) => {
                    formData.append(`files`, file);
                });
            }
            console.log("formData: ", formData);
            // Gửi yêu cầu đến API và đọc phản hồi thực tế
            const response = await fetch(apiUrl, {
                method: "POST",
                body: formData,
            });

            // Kiểm tra trạng thái phản hồi
            if (!response.ok) {
                throw new Error(
                    `API error: ${response.status} ${response.statusText}`
                );
            }

            // Xử lý dữ liệu từ phản hồi
            const data = await response.json();

            // Kiểm tra và trả về trường output nếu có
            if (data && data.output) {
                return data.output;
            } else if (data) {
                // Nếu không có trường output, trả về toàn bộ phản hồi dạng chuỗi
                console.log("Phản hồi API không chứa trường output:", data);
                return JSON.stringify(data, null, 2);
            } else {
                return "Đã nhận được phản hồi từ API nhưng không có dữ liệu.";
            }
        } catch (error) {
            console.error("Lỗi khi gọi API:", error);
            return `Đã xảy ra lỗi khi gọi API: ${error.message}. Vui lòng thử lại sau.`;
        }
    }

    // Thêm hàm lưu tin nhắn của phiên chat hiện tại
    function saveCurrentChatMessages() {
        const activeChat = document.querySelector(".conversation-item.active");
        if (!activeChat) return;

        const chatId = activeChat.getAttribute("data-id");

        // Kiểm tra xem có tin nhắn nào không
        if (
            chatMessages.children.length === 0 ||
            (chatMessages.children.length === 1 &&
                chatMessages.querySelector(".chat-welcome"))
        ) {
            return; // Không có tin nhắn để lưu
        }

        const messages = [];
        Array.from(chatMessages.children).forEach((message) => {
            // Bỏ qua phần tử welcome và typing indicator
            if (
                !message.classList.contains("chat-welcome") &&
                !message.classList.contains("typing-indicator")
            ) {
                const isBot = message.classList.contains("bot");
                const content =
                    message.querySelector(".markdown-content")?.innerHTML || "";
                const time =
                    message.querySelector(".message-time")?.textContent ||
                    getCurrentTime();
                messages.push({
                    sender: isBot ? "bot" : "user",
                    content: content,
                    time: time,
                });
            }
        });

        const conversations = JSON.parse(
            localStorage.getItem("conversations") || "[]"
        );
        const chatIndex = conversations.findIndex(
            (c) => c.id === parseInt(chatId)
        );
        if (chatIndex !== -1) {
            conversations[chatIndex].messages = messages;
            localStorage.setItem(
                "conversations",
                JSON.stringify(conversations)
            );
        }
    }

    // Thêm hàm khôi phục tin nhắn của phiên chat
    function restoreChatMessages(chatId) {
        const conversations = JSON.parse(
            localStorage.getItem("conversations") || "[]"
        );
        const chat = conversations.find((c) => c.id === parseInt(chatId));

        // Xóa tất cả tin nhắn hiện tại
        chatMessages.innerHTML = "";

        if (chat && chat.messages && chat.messages.length > 0) {
            // Khôi phục tin nhắn từ localStorage
            chat.messages.forEach((message) => {
                const messageDiv = document.createElement("div");
                messageDiv.classList.add("message", message.sender);

                // Tạo id duy nhất cho tin nhắn
                const messageId = Date.now() + Math.floor(Math.random() * 1000);
                messageDiv.setAttribute("data-message-id", messageId);

                const messageContent = document.createElement("div");
                messageContent.classList.add("message-content");

                const markdownContent = document.createElement("div");
                markdownContent.classList.add("markdown-content");

                // Kiểm tra nếu tin nhắn có file
                const hasFiles = message.files && message.files.length > 0;
                if (hasFiles) {
                    markdownContent.classList.add("has-files");
                }

                // Xử lý nội dung tin nhắn
                if (message.sender === "bot") {
                    try {
                        // Nếu nội dung chưa được parse
                        if (!message.content.includes("<")) {
                            markdownContent.innerHTML = marked.parse(
                                message.content
                            );
                        } else {
                            markdownContent.innerHTML = message.content;
                        }

                        // Highlight tất cả code blocks
                        setTimeout(() => {
                            const codeBlocks =
                                markdownContent.querySelectorAll("pre code");
                            if (codeBlocks.length > 0) {
                                codeBlocks.forEach((codeBlock) => {
                                    hljs.highlightElement(codeBlock);
                                });
                            }
                        }, 0);
                    } catch (error) {
                        console.error(
                            "Lỗi khi khôi phục nội dung markdown:",
                            error
                        );
                        markdownContent.innerHTML = message.content;
                    }
                } else {
                    // Nếu là tin nhắn người dùng, hiển thị dạng text thông thường
                    if (!message.content.includes("<")) {
                        markdownContent.textContent = message.content;
                    } else {
                        markdownContent.innerHTML = message.content;
                    }
                }

                const messageTime = document.createElement("div");
                messageTime.classList.add("message-time");
                messageTime.textContent = message.time;

                messageContent.appendChild(markdownContent);
                messageDiv.appendChild(messageContent);
                messageDiv.appendChild(messageTime);

                // Thêm đánh giá cho tin nhắn bot nếu tính năng được bật
                if (message.sender === "bot" && showRatings) {
                    addRatingToMessage(messageContent, messageId);
                }

                chatMessages.appendChild(messageDiv);
            });
        } else {
            // Nếu không có tin nhắn, hiển thị trang welcome
            if (chatWelcome) {
                chatWelcome.style.display = "block";
            }
        }
    }

    // Hàm cập nhật currentChatId
    function updateCurrentChatId() {
        const activeChat = document.querySelector(".conversation-item.active");
        if (activeChat) {
            currentChatId = parseInt(activeChat.getAttribute("data-id"));
            return currentChatId;
        }
        return null;
    }

    // Hàm khởi tạo chats từ localStorage
    function initializeChats() {
        const conversations = JSON.parse(
            localStorage.getItem("conversations") || "[]"
        );
        conversations.forEach((conv) => {
            chats[conv.id] = {
                name: conv.name,
                messages: conv.messages || [],
            };
        });
        // Cập nhật currentChatId
        updateCurrentChatId();
    }

    // Hàm lưu chats vào localStorage
    function saveChats() {
        const conversations = [];
        for (const id in chats) {
            conversations.push({
                id: parseInt(id),
                name: chats[id].name,
                messages: chats[id].messages,
            });
        }
        localStorage.setItem("conversations", JSON.stringify(conversations));
    }

    // Hàm gửi tin nhắn
    function sendMessage() {
        const message = userInput.value.trim();
        const sectionName = document.querySelector(".main-title").textContent;
        // Sử dụng biến uploadedFiles thay vì uploadBtn.files
        if (message === "" && uploadedFiles.length === 0) return;

        // Đảm bảo currentChatId được cập nhật
        const originalChatId = updateCurrentChatId();
        if (!originalChatId) {
            // Nếu không có chat active, tạo chat mới
            createNewChat();
            updateCurrentChatId();
        }

        // Tạo bản sao của mảng files
        const filesArray = [...uploadedFiles];

        // Tạo nội dung tin nhắn với thông tin file (nếu có)
        let fullMessage = message;

        // Nếu có file đính kèm, thêm thông tin file vào tin nhắn
        if (filesArray.length > 0) {
            // Tạo danh sách file để hiển thị
            const fileNames = filesArray.map((file) => file.name).join(", ");
            if (message) {
                fullMessage += "\n\n";
            }
            fullMessage += `📎 File đính kèm: ${
                filesArray.length > 1 ? filesArray.length + " files" : fileNames
            }`;
        }

        // Thêm tin nhắn của người dùng
        const messageId = addMessage(fullMessage, "user", filesArray);

        // Lưu ngay tin nhắn của người dùng (với thông tin file)
        saveUserMessage(
            originalChatId,
            fullMessage,
            filesArray.map((file) => file.name)
        );

        // Xóa nội dung input
        userInput.value = "";

        // Xử lý files đã chọn
        if (filesArray.length > 0) {
            // Xóa indicator file sau khi gửi
            const fileIndicator = document.querySelector(
                ".file-indicator-wrapper"
            );
            if (fileIndicator) {
                fileIndicator.remove();
            }
            // Reset danh sách files sau khi gửi
            uploadedFiles = [];
        }

        // Hiển thị đang nhập
        showTypingIndicator();

        // Gọi API thực tế thay vì giả lập
        (async () => {
            try {
                const response = await callChatAPI(
                    message,
                    sectionName,
                    filesArray
                );

                // Kiểm tra xem người dùng có chuyển sang cuộc trò chuyện khác không
                if (originalChatId === updateCurrentChatId()) {
                    // Nếu người dùng vẫn ở cùng một cuộc trò chuyện
                    addMessage(response, "bot");
                    // Lưu tin nhắn của bot
                    saveBotMessage(originalChatId, response);
                    // Cập nhật hiển thị đánh giá
                    updateRatingDisplay();
                } else {
                    // Nếu người dùng đã chuyển sang cuộc trò chuyện khác
                    // Vẫn lưu tin nhắn của bot vào cuộc trò chuyện ban đầu
                    saveBotMessage(originalChatId, response);
                }
            } catch (error) {
                console.error("Lỗi khi gọi API:", error);
                const errorMessage = `Đã xảy ra lỗi khi gọi API: ${error.message}. Vui lòng thử lại sau.`;

                if (originalChatId === updateCurrentChatId()) {
                    addMessage(errorMessage, "bot");
                    saveBotMessage(originalChatId, errorMessage);
                    updateRatingDisplay();
                } else {
                    saveBotMessage(originalChatId, errorMessage);
                }
            } finally {
                // Ẩn đang nhập
                hideTypingIndicator();
            }
        })();
    }

    // Lưu tin nhắn của người dùng
    function saveUserMessage(chatId, message, fileNames = []) {
        if (!chatId || (!message && fileNames.length === 0)) return;

        // Kiểm tra xem chat có tồn tại không
        if (!chats[chatId]) {
            chats[chatId] = {
                name: "Cuộc trò chuyện mới",
                messages: [],
            };
        }

        // Thêm tin nhắn vào mảng
        chats[chatId].messages.push({
            content: message,
            sender: "user",
            time: getCurrentTime(),
            files: fileNames,
        });

        // Lưu vào localStorage
        saveChats();
    }

    // Lưu tin nhắn của bot
    function saveBotMessage(chatId, message) {
        if (!chatId || !message) return;

        // Kiểm tra xem chat có tồn tại không
        if (!chats[chatId]) {
            chats[chatId] = {
                name: "Cuộc trò chuyện mới",
                messages: [],
            };
        }

        // Thêm tin nhắn vào mảng
        chats[chatId].messages.push({
            content: message,
            sender: "bot",
            time: getCurrentTime(),
        });

        // Lưu vào localStorage
        saveChats();
    }

    // Hiển thị typing indicator
    function showTypingIndicator() {
        const typingDiv = document.createElement("div");
        typingDiv.className = "typing-indicator";
        typingDiv.innerHTML = `
            <span></span>
            <span></span>
            <span></span>
        `;

        if (chatWelcome) {
            chatWelcome.style.display = "none";
        }

        chatMessages.appendChild(typingDiv);
        scrollToBottom();
    }

    // Ẩn typing indicator
    function hideTypingIndicator() {
        const typingIndicator = document.querySelector(".typing-indicator");
        if (typingIndicator) {
            typingIndicator.remove();
        }
    }

    // Reset độ cao của input
    function resetInputHeight() {
        userInput.style.height = "auto";
    }

    // Thêm tin nhắn vào khu vực chat
    function addMessage(content, sender, files = []) {
        const messageDiv = document.createElement("div");
        messageDiv.classList.add("message", sender);

        // Tạo id duy nhất cho tin nhắn
        const messageId = Date.now() + Math.floor(Math.random() * 1000);
        messageDiv.setAttribute("data-message-id", messageId);

        const messageContent = document.createElement("div");
        messageContent.classList.add("message-content");

        const markdownContent = document.createElement("div");
        markdownContent.classList.add("markdown-content");

        // Xử lý nội dung tin nhắn
        if (sender === "bot") {
            try {
                // Sử dụng marked để parse markdown
                markdownContent.innerHTML = marked.parse(content);

                // Highlight tất cả code blocks
                setTimeout(() => {
                    const codeBlocks =
                        markdownContent.querySelectorAll("pre code");
                    if (codeBlocks.length > 0) {
                        codeBlocks.forEach((codeBlock) => {
                            hljs.highlightElement(codeBlock);
                        });
                    }
                }, 0);
            } catch (error) {
                console.error("Lỗi khi parse markdown:", error);
                markdownContent.textContent = content;
            }
        } else {
            // Nội dung thông thường cho tin nhắn người dùng
            markdownContent.textContent = content;

            // Nếu có file, hiển thị biểu tượng file
            if (files && files.length > 0) {
                markdownContent.classList.add("has-files");
            }
        }

        messageContent.appendChild(markdownContent);

        const messageTime = document.createElement("div");
        messageTime.classList.add("message-time");
        messageTime.textContent = getCurrentTime();

        messageDiv.appendChild(messageContent);
        messageDiv.appendChild(messageTime);

        // Thêm đánh giá cho tin nhắn bot nếu tính năng được bật
        if (sender === "bot" && showRatings) {
            addRatingToMessage(messageContent, messageId);
        }

        // Ẩn trang welcome nếu nó đang hiển thị
        if (chatWelcome) {
            chatWelcome.style.display = "none";
        }

        chatMessages.appendChild(messageDiv);

        // Cuộn xuống tin nhắn mới nhất
        scrollToBottom();

        return messageId;
    }

    // Hàm thêm đánh giá vào tin nhắn
    function addRatingToMessage(messageContent, messageId) {
        const ratingDiv = document.createElement("div");
        ratingDiv.className = "message-rating";

        ratingDiv.innerHTML = `
            <div class="message-rating-label">Đánh giá:</div>
            <div class="rating-stars" data-message-id="${messageId}">
                <div class="rating-emoji"></div>
                <i class="fas fa-star rating-star" data-value="1" data-emoji="😞"></i>
                <i class="fas fa-star rating-star" data-value="2" data-emoji="😐"></i>
                <i class="fas fa-star rating-star" data-value="3" data-emoji="🙂"></i>
                <i class="fas fa-star rating-star" data-value="4" data-emoji="😊"></i>
                <i class="fas fa-star rating-star" data-value="5" data-emoji="😍"></i>
            </div>
            <div class="rating-submitted"></div>
        `;
        messageContent.appendChild(ratingDiv);

        // Thêm sự kiện cho các ngôi sao
        const stars = ratingDiv.querySelectorAll(".rating-star");
        const emojiEl = ratingDiv.querySelector(".rating-emoji");
        const ratingSubmitted = ratingDiv.querySelector(".rating-submitted");

        stars.forEach((star) => {
            // Hiệu ứng hover emoji
            star.addEventListener("mouseenter", function () {
                const emoji = this.getAttribute("data-emoji");
                emojiEl.textContent = emoji;
            });

            // Sự kiện click để đánh giá
            star.addEventListener("click", function () {
                const value = parseInt(this.getAttribute("data-value"));
                const emoji = this.getAttribute("data-emoji");

                // Xóa lớp active từ tất cả các ngôi sao
                stars.forEach((s) => s.classList.remove("active"));

                // Thêm lớp active cho các ngôi sao được chọn
                stars.forEach((s) => {
                    if (parseInt(s.getAttribute("data-value")) <= value) {
                        s.classList.add("active");
                    }
                });

                // Hiển thị emoji tương ứng với đánh giá
                emojiEl.textContent = emoji;

                // Thêm thông báo đã gửi đánh giá (hoặc thông báo đánh giá lại)
                const previousRating = messageRatings[messageId];
                if (previousRating && previousRating !== value) {
                    ratingSubmitted.textContent = "Đã cập nhật!";
                } else {
                    ratingSubmitted.textContent = "Đã gửi!";
                }
                ratingSubmitted.classList.add("show");

                // Lưu đánh giá
                saveRating(messageId, value);

                // Sau 2 giây, ẩn thông báo nhưng giữ nguyên đánh giá
                setTimeout(() => {
                    ratingSubmitted.classList.remove("show");
                }, 2000);
            });
        });

        // Sự kiện khi rời chuột khỏi vùng rating
        ratingDiv
            .querySelector(".rating-stars")
            .addEventListener("mouseleave", function () {
                // Nếu có ngôi sao active, hiển thị emoji của ngôi sao cao nhất active
                const activeStars = this.querySelectorAll(
                    ".rating-star.active"
                );
                if (activeStars.length > 0) {
                    const highestStar = activeStars[activeStars.length - 1];
                    emojiEl.textContent =
                        highestStar.getAttribute("data-emoji");
                } else {
                    emojiEl.textContent = "";
                }
            });

        // Kiểm tra và hiển thị đánh giá đã lưu nếu có
        const existingRating = messageRatings[messageId];
        if (existingRating) {
            applyRating(stars, emojiEl, existingRating);
        }
    }

    // Hàm áp dụng đánh giá lên giao diện
    function applyRating(stars, emojiEl, rating) {
        // Xóa lớp active từ tất cả các ngôi sao
        stars.forEach((s) => s.classList.remove("active"));

        // Thêm lớp active cho các ngôi sao được chọn
        stars.forEach((s) => {
            if (parseInt(s.getAttribute("data-value")) <= rating) {
                s.classList.add("active");
            }
        });

        // Hiển thị emoji tương ứng
        const ratedStar = [...stars].find(
            (s) => parseInt(s.getAttribute("data-value")) === rating
        );
        if (ratedStar) {
            emojiEl.textContent = ratedStar.getAttribute("data-emoji");
        }

        // Thêm dòng gợi ý đánh giá lại vào parent
        const ratingStars = stars[0].closest(".rating-stars");
        let ratingHint = ratingStars.querySelector(".rating-hint");

        if (!ratingHint) {
            ratingHint = document.createElement("div");
            ratingHint.className = "rating-hint";
            ratingHint.textContent = "Nhấp để đánh giá lại";
            ratingHint.style.fontSize = "11px";
            ratingHint.style.color = "var(--text-secondary)";
            ratingHint.style.textAlign = "center";
            ratingHint.style.marginTop = "5px";
            ratingHint.style.opacity = "0";
            ratingHint.style.transition = "opacity 0.3s";

            ratingStars.appendChild(ratingHint);

            // Hiển thị gợi ý khi hover
            ratingStars.addEventListener("mouseenter", () => {
                ratingHint.style.opacity = "0.8";
            });

            ratingStars.addEventListener("mouseleave", () => {
                ratingHint.style.opacity = "0";
            });
        }
    }

    // Hàm lưu đánh giá
    function saveRating(messageId, rating) {
        // Kiểm tra nếu đây là lần đánh giá lại
        const isRerate =
            messageRatings[messageId] !== undefined &&
            messageRatings[messageId] !== rating;

        console.log(
            `${
                isRerate ? "Đánh giá lại" : "Đánh giá"
            } tin nhắn ${messageId} với số sao: ${rating}`
        );

        // Lưu đánh giá vào messageRatings
        messageRatings[messageId] = rating;

        // Lưu vào localStorage
        try {
            localStorage.setItem(
                "messageRatings",
                JSON.stringify(messageRatings)
            );
        } catch (e) {
            console.error("Không thể lưu đánh giá:", e);
        }

        // Tại đây có thể thêm code để gửi đánh giá đến server
        if (isRerate) {
            // Gửi thông tin về việc đánh giá lại tới server (trong tương lai)
            console.log(
                `Người dùng đã thay đổi đánh giá tin nhắn ${messageId}`
            );
        }
    }

    // Cập nhật hiển thị đánh giá dựa trên trạng thái của toggle
    function updateRatingDisplay() {
        const botMessages = document.querySelectorAll(".message.bot");

        botMessages.forEach((msg) => {
            let ratingDiv = msg.querySelector(".message-rating");
            let messageId = msg.getAttribute("data-message-id");

            if (!messageId) {
                // Nếu tin nhắn chưa có ID, tạo ID mới
                messageId = Date.now() + Math.floor(Math.random() * 1000);
                msg.setAttribute("data-message-id", messageId);
            }

            if (showRatings) {
                // Nếu đang bật đánh giá mà chưa có phần đánh giá, thêm vào
                if (!ratingDiv) {
                    const messageContent =
                        msg.querySelector(".message-content");
                    addRatingToMessage(messageContent, messageId);
                } else {
                    // Nếu đã có phần đánh giá, chỉ cần hiển thị lại
                    ratingDiv.style.display = "flex";

                    // Kiểm tra và hiển thị đánh giá đã lưu nếu có
                    const stars = ratingDiv.querySelectorAll(".rating-star");
                    const emojiEl = ratingDiv.querySelector(".rating-emoji");
                    const ratingStars =
                        ratingDiv.querySelector(".rating-stars");

                    if (ratingStars) {
                        const ratingId =
                            ratingStars.getAttribute("data-message-id");
                        const existingRating = messageRatings[ratingId];

                        if (existingRating) {
                            applyRating(stars, emojiEl, existingRating);
                        }
                    }
                }
            } else {
                // Nếu đang tắt đánh giá mà có phần đánh giá, ẩn đi
                if (ratingDiv) {
                    ratingDiv.style.display = "none";
                }
            }
        });
    }

    // Lấy thời gian hiện tại theo định dạng HH:MM
    function getCurrentTime() {
        const now = new Date();
        let hours = now.getHours();
        let minutes = now.getMinutes();

        hours = hours < 10 ? "0" + hours : hours;
        minutes = minutes < 10 ? "0" + minutes : minutes;

        return `${hours}:${minutes}`;
    }

    // Cuộn xuống tin nhắn mới nhất
    function scrollToBottom() {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    // Thêm hàm cập nhật tiêu đề chat
    function updateChatTitle(conversationName) {
        const mainTitle = document.querySelector(".main-title");
        if (mainTitle) {
            mainTitle.textContent = conversationName;
        }
    }

    // Thêm hàm kiểm tra tên phiên chat đã tồn tại chưa
    function isChatNameExists(name) {
        const conversations = JSON.parse(
            localStorage.getItem("conversations") || "[]"
        );
        return conversations.some(
            (chat) => chat.name.toLowerCase() === name.toLowerCase()
        );
    }

    // Tạo tên phiên chat độc nhất
    function generateUniqueChatName(baseName) {
        let nameToUse = baseName;
        let counter = 1;

        while (isChatNameExists(nameToUse)) {
            nameToUse = `${baseName} (${counter})`;
            counter++;
        }

        return nameToUse;
    }

    // Tạo hội thoại mới
    function createNewChat() {
        // Lưu tin nhắn của phiên chat hiện tại trước khi tạo mới
        saveCurrentChatMessages();

        // Tạo ID mới cho hội thoại
        const newId = Date.now();

        // Tạo tên phiên chat độc nhất
        const uniqueName = generateUniqueChatName("Hội thoại mới");

        // Tạo element mới cho hội thoại
        const newConversation = document.createElement("div");
        newConversation.className = "conversation-item";
        newConversation.setAttribute("data-id", newId);
        newConversation.innerHTML = `
            <i class="fas fa-comment-alt"></i>
            <span class="conversation-name">${uniqueName}</span>
            <div class="conversation-actions">
                <button class="edit-name-btn" title="Chỉnh sửa tên">
                    <i class="fas fa-edit"></i>
                </button>
                <button class="delete-chat-btn" title="Xóa hội thoại">
                    <i class="fas fa-trash"></i>
                </button>
            </div>
        `;

        // Thêm vào đầu danh sách
        const conversationsList = document.getElementById("conversations-list");
        conversationsList.insertBefore(
            newConversation,
            conversationsList.firstChild
        );

        // Lưu vào localStorage
        const conversations = JSON.parse(
            localStorage.getItem("conversations") || "[]"
        );
        conversations.unshift({
            id: newId,
            name: uniqueName,
            messages: [],
        });
        localStorage.setItem("conversations", JSON.stringify(conversations));

        // Kích hoạt chat mới
        document.querySelectorAll(".conversation-item").forEach((item) => {
            item.classList.remove("active");
        });
        newConversation.classList.add("active");

        // Cập nhật tiêu đề chat
        updateChatTitle(uniqueName);

        // Xóa tất cả tin nhắn và hiển thị welcome screen
        chatMessages.innerHTML = "";
        if (chatWelcome) {
            chatWelcome.style.display = "block";
        }

        // Reset input
        userInput.value = "";
        resetInputHeight();

        // Cập nhật lại sự kiện cho tất cả các phiên chat
        addEventListenersToConversations();

        // Cập nhật lại biến theo dõi các phiên chat
        conversationItems = updateConversationItemsReference();
    }

    // Chỉnh sửa tên hội thoại
    function editConversationName(conversationItem) {
        const nameSpan = conversationItem.querySelector(".conversation-name");
        const currentName = nameSpan.textContent;

        // Tạo input để chỉnh sửa
        const input = document.createElement("input");
        input.type = "text";
        input.value = currentName;
        input.className = "edit-name-input";

        // Thay thế span bằng input
        nameSpan.replaceWith(input);
        input.focus();

        // Xử lý khi nhấn Enter hoặc click ra ngoài
        function saveName() {
            if (input.parentNode) {
                // Kiểm tra xem input còn tồn tại không
                let newName = input.value.trim() || "Hội thoại mới";

                // Lấy danh sách hội thoại
                const conversations = JSON.parse(
                    localStorage.getItem("conversations") || "[]"
                );
                const id = conversationItem.getAttribute("data-id");
                const currentChatId = parseInt(id);

                // Kiểm tra xem tên mới có trùng với tên hội thoại khác không (trừ chính nó)
                const isDuplicate = conversations.some(
                    (chat) =>
                        chat.id !== currentChatId &&
                        chat.name.toLowerCase() === newName.toLowerCase()
                );

                // Nếu trùng, tạo tên độc nhất
                if (isDuplicate) {
                    newName = generateUniqueChatName(newName);
                    alert(
                        `Tên hội thoại đã tồn tại. Đã đổi thành "${newName}"`
                    );
                }

                // Tạo span mới với tên đã kiểm tra
                const newSpan = document.createElement("span");
                newSpan.className = "conversation-name";
                newSpan.textContent = newName;
                input.replaceWith(newSpan);

                // Cập nhật tiêu đề chat nếu đang active
                if (conversationItem.classList.contains("active")) {
                    updateChatTitle(newName);
                }

                // Lưu tên mới vào localStorage
                const index = conversations.findIndex(
                    (c) => c.id === currentChatId
                );
                if (index !== -1) {
                    conversations[index].name = newName;
                    localStorage.setItem(
                        "conversations",
                        JSON.stringify(conversations)
                    );
                }
            }
        }

        // Đảm bảo chỉ lưu tên một lần
        let isSaved = false;

        input.addEventListener("blur", function () {
            if (!isSaved) {
                isSaved = true;
                saveName();
            }
        });

        input.addEventListener("keypress", function (e) {
            if (e.key === "Enter" && !isSaved) {
                isSaved = true;
                saveName();
            }
        });
    }

    // Thêm hàm để xóa một hội thoại cụ thể
    function deleteConversation(conversationItem) {
        // Lấy ID của hội thoại cần xóa
        const chatId = conversationItem.getAttribute("data-id");

        // Xác nhận trước khi xóa
        if (!confirm("Bạn có chắc muốn xóa hội thoại này?")) {
            return;
        }

        // Xóa khỏi localStorage
        const conversations = JSON.parse(
            localStorage.getItem("conversations") || "[]"
        );
        const updatedConversations = conversations.filter(
            (c) => c.id !== parseInt(chatId)
        );

        // Nếu đã xóa hết tất cả hội thoại, tạo một hội thoại mặc định
        if (updatedConversations.length === 0) {
            createNewChat();
            return;
        }

        localStorage.setItem(
            "conversations",
            JSON.stringify(updatedConversations)
        );

        // Xóa khỏi DOM
        conversationItem.remove();

        // Nếu xóa hội thoại đang active, chuyển sang hội thoại đầu tiên
        if (conversationItem.classList.contains("active")) {
            const firstConversation =
                document.querySelector(".conversation-item");
            if (firstConversation) {
                firstConversation.classList.add("active");
                const name =
                    firstConversation.querySelector(
                        ".conversation-name"
                    ).textContent;
                updateChatTitle(name);

                // Hiển thị tin nhắn của hội thoại đầu tiên
                const firstChatId = firstConversation.getAttribute("data-id");
                restoreChatMessages(firstChatId);
            }
        }

        // Cập nhật lại biến theo dõi các phiên chat
        conversationItems = updateConversationItemsReference();
    }

    // Thêm hàm thêm event listeners
    function addEventListenersToConversations() {
        const items = document.querySelectorAll(".conversation-item");

        items.forEach((item) => {
            // Xóa event listeners cũ nếu có
            const newItem = item.cloneNode(true);
            item.parentNode.replaceChild(newItem, item);

            // Xử lý click vào hội thoại
            newItem.addEventListener("click", function (e) {
                if (
                    !e.target.closest(".edit-name-btn") &&
                    !e.target.closest(".delete-chat-btn")
                ) {
                    // Lưu tin nhắn của phiên chat hiện tại
                    saveCurrentChatMessages();

                    // Chỉ xóa active từ các hội thoại khác
                    document
                        .querySelectorAll(".conversation-item")
                        .forEach((i) => i.classList.remove("active"));
                    this.classList.add("active");

                    // Cập nhật tiêu đề chat
                    const conversationName =
                        this.querySelector(".conversation-name").textContent;
                    updateChatTitle(conversationName);

                    // Khôi phục tin nhắn của phiên chat được chọn
                    const chatId = this.getAttribute("data-id");
                    restoreChatMessages(chatId);

                    // Reset input
                    userInput.value = "";
                    resetInputHeight();
                }
            });

            // Xử lý click vào nút chỉnh sửa tên
            const editBtn = newItem.querySelector(".edit-name-btn");
            editBtn.addEventListener("click", function (e) {
                e.stopPropagation();
                editConversationName(newItem);
            });

            // Xử lý click vào nút xóa hội thoại
            const deleteBtn = newItem.querySelector(".delete-chat-btn");
            if (deleteBtn) {
                deleteBtn.addEventListener("click", function (e) {
                    e.stopPropagation();
                    deleteConversation(newItem);
                });
            }
        });
    }

    // Khởi tạo các sự kiện cho danh sách hội thoại
    function initializeConversations() {
        addEventListenersToConversations();

        // Đảm bảo trạng thái active của chat đầu tiên
        const firstConversation = document.querySelector(".conversation-item");
        if (firstConversation) {
            firstConversation.classList.add("active");
            const name =
                firstConversation.querySelector(
                    ".conversation-name"
                ).textContent;
            updateChatTitle(name);
        }
    }

    // Thêm hàm khôi phục các phiên chat từ localStorage khi trang tải
    function loadConversationsFromStorage() {
        const conversations = JSON.parse(
            localStorage.getItem("conversations") || "[]"
        );
        if (conversations.length === 0) {
            // Nếu không có phiên chat nào, tạo phiên chat mặc định
            const defaultId = 1;
            const defaultName = "Hội thoại đầu tiên";
            conversations.push({
                id: defaultId,
                name: defaultName,
                messages: [],
            });
            localStorage.setItem(
                "conversations",
                JSON.stringify(conversations)
            );
            return;
        }

        // Xóa các phiên chat mặc định trong HTML
        const conversationsList = document.getElementById("conversations-list");
        conversationsList.innerHTML = "";

        // Thêm các phiên chat từ localStorage vào DOM
        conversations.forEach((chat) => {
            const conversationItem = document.createElement("div");
            conversationItem.className = "conversation-item";
            conversationItem.setAttribute("data-id", chat.id);

            if (conversations.indexOf(chat) === 0) {
                conversationItem.classList.add("active");
            }

            conversationItem.innerHTML = `
                <i class="fas fa-comment-alt"></i>
                <span class="conversation-name">${chat.name}</span>
                <div class="conversation-actions">
                    <button class="edit-name-btn" title="Chỉnh sửa tên">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button class="delete-chat-btn" title="Xóa hội thoại">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            `;

            conversationsList.appendChild(conversationItem);
        });

        // Cập nhật lại danh sách các phiên chat
        conversationItems = updateConversationItemsReference();

        // Thêm event listeners cho các phiên chat
        addEventListenersToConversations();

        // Hiển thị tin nhắn của phiên chat đầu tiên nếu có
        const firstChat = document.querySelector(".conversation-item.active");
        if (firstChat) {
            const chatId = firstChat.getAttribute("data-id");
            restoreChatMessages(chatId);
            const chatName =
                firstChat.querySelector(".conversation-name").textContent;
            updateChatTitle(chatName);
        }
    }

    // Khởi tạo khi trang tải
    loadConversationsFromStorage();
    initializeConversations();
    initializeChats();
    restoreSettings();
    restoreRatings();
    updateRatingDisplay();

    // Xử lý sự kiện
    sendBtn.addEventListener("click", sendMessage);

    userInput.addEventListener("keypress", function (e) {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    // Auto-resize textarea
    userInput.addEventListener("input", function () {
        this.style.height = "auto";
        this.style.height = this.scrollHeight + "px";
        if (this.scrollHeight > 150) {
            this.style.height = "150px";
        }
    });

    // Xử lý chế độ tối
    function toggleDarkMode() {
        document.body.classList.toggle("dark-mode");
        const isDarkMode = document.body.classList.contains("dark-mode");
        localStorage.setItem("darkMode", isDarkMode);
    }

    // Toggle sidebar trên mobile
    if (toggleSidebarBtn) {
        toggleSidebarBtn.addEventListener("click", function () {
            sidebar.classList.toggle("active");
        });
    }

    // Toggle user dropdown
    if (userAvatar) {
        // Khôi phục xử lý hiển thị dropdown khi click vào avatar
        userAvatar.addEventListener("click", function () {
            userDropdown.classList.toggle("active");
        });

        // Khôi phục xử lý đóng dropdown khi click bên ngoài
        document.addEventListener("click", function (e) {
            if (
                !userAvatar.contains(e.target) &&
                !userDropdown.contains(e.target)
            ) {
                userDropdown.classList.remove("active");
            }
        });
    }

    // Xử lý các suggestion cards
    if (suggestionCards.length > 0) {
        suggestionCards.forEach((card) => {
            card.addEventListener("click", function () {
                const exampleElement = this.querySelector(
                    ".suggestion-examples p:first-child"
                );
                if (exampleElement) {
                    const exampleText = exampleElement.textContent.replace(
                        /"/g,
                        ""
                    );
                    userInput.value = exampleText;
                    userInput.focus();
                }
            });
        });
    }

    // Xử lý nút tạo hội thoại mới
    if (newChatBtn) {
        // Xóa event listeners cũ
        const newChatBtnClone = newChatBtn.cloneNode(true);
        newChatBtn.parentNode.replaceChild(newChatBtnClone, newChatBtn);

        // Thêm event listener mới
        newChatBtnClone.addEventListener("click", function () {
            createNewChat();
        });
    }

    // Settings panel
    settingsBtn.addEventListener("click", function () {
        settingsPanel.classList.add("active");
        updateSettingsPanel();
    });

    closeSettingsBtn.addEventListener("click", function () {
        settingsPanel.classList.remove("active");
    });

    // Khôi phục cài đặt từ localStorage
    function restoreSettings() {
        // Khôi phục cài đặt chế độ tối
        const darkMode = localStorage.getItem("darkMode") === "true";
        if (darkMode) {
            document.body.classList.add("dark-mode");
            darkModeToggle.checked = true;
        }

        // Khôi phục kích thước font
        const fontSize = localStorage.getItem("fontSize") || "medium";
        fontSizeSelect.value = fontSize;
        document.documentElement.classList.remove(
            "font-small",
            "font-medium",
            "font-large"
        );
        document.documentElement.classList.add(`font-${fontSize}`);

        // Khôi phục cài đặt đánh giá
        const showRatingsSetting = localStorage.getItem("showRatings");
        showRatings = showRatingsSetting === "true";
        ratingToggle.checked = showRatings;

        // Khôi phục trạng thái Think
        const thinkSetting = localStorage.getItem("thinkEnabled");
        thinkEnabled = thinkSetting === "true";
        if (thinkEnabled) {
            thinkToggleBtn.classList.add("active");
        } else {
            thinkToggleBtn.classList.remove("active");
        }

        updateRatingDisplay();
    }

    // Dark mode toggle in settings
    if (darkModeToggle) {
        darkModeToggle.addEventListener("change", function () {
            const isDarkMode = this.checked;
            document.body.classList.toggle("dark-mode", isDarkMode);
            localStorage.setItem("darkMode", isDarkMode);
        });
    }

    // Rating toggle in settings
    if (ratingToggle) {
        ratingToggle.addEventListener("change", function () {
            showRatings = this.checked;
            localStorage.setItem("showRatings", showRatings);

            // Cập nhật hiển thị đánh giá khi toggle thay đổi
            updateRatingDisplay();
        });
    }

    // Font size change
    fontSizeSelect.addEventListener("change", function () {
        const size = this.value;
        document.documentElement.style.setProperty(
            "--font-size-medium",
            size === "small" ? "14px" : size === "large" ? "18px" : "16px"
        );
        localStorage.setItem("fontSize", size);
    });

    // Export chat
    exportChatBtn.addEventListener("click", function () {
        // Tạo nội dung từ tin nhắn
        let content = "# Chat History\n\n";

        const messages = document.querySelectorAll(".message");
        if (messages.length === 0) {
            alert("Không có tin nhắn nào để xuất.");
            return;
        }

        messages.forEach((message) => {
            const isBot = message.classList.contains("bot");
            const msgContent = message.querySelector(".markdown-content");
            const time = message.querySelector(".message-time").textContent;

            content += `## ${isBot ? "Bot" : "User"} (${time})\n`;
            content += isBot ? msgContent.innerHTML : msgContent.textContent;
            content += "\n\n---\n\n";
        });

        // Tạo và tải xuống file
        const blob = new Blob([content], { type: "text/markdown" });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `chat-history-${new Date().toISOString().slice(0, 10)}.md`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    });

    // Clear history
    clearHistoryBtn.addEventListener("click", function () {
        if (
            confirm(
                "Xóa lịch sử chat sẽ xóa tất cả tin nhắn. Bạn có chắc không?"
            )
        ) {
            createNewChat();
        }
    });

    // Upload button
    uploadBtn.addEventListener("click", function () {
        const input = document.createElement("input");
        input.type = "file";
        input.multiple = true; // Cho phép upload nhiều file
        input.accept = "image/*,.pdf,.doc,.docx,.txt";
        input.onchange = function (e) {
            const files = Array.from(e.target.files);
            if (files.length > 0) {
                // Lưu file để gửi kèm với tin nhắn tiếp theo
                uploadedFiles = [...uploadedFiles, ...files];

                // Ẩn trang welcome nếu đang hiển thị
                if (chatWelcome && chatWelcome.style.display !== "none") {
                    chatWelcome.style.display = "none";
                }

                // Hiển thị thông báo file đính kèm
                showFileAttachmentIndicator(files);
            }
        };
        input.click();
    });

    // Hiển thị indicator cho files đính kèm
    function showFileAttachmentIndicator(files) {
        // Xóa indicator cũ nếu có
        const oldIndicator = document.querySelector(".file-indicator-wrapper");
        if (oldIndicator) {
            oldIndicator.remove();
        }

        // Tạo wrapper để căn giữa
        const fileIndicatorWrapper = document.createElement("div");
        fileIndicatorWrapper.className = "file-indicator-wrapper";

        // Tạo indicator mới
        const fileIndicator = document.createElement("div");
        fileIndicator.className = "file-indicator";

        // Hiển thị danh sách files
        const fileList = document.createElement("div");
        fileList.className = "file-list";

        files.forEach((file) => {
            const fileItem = document.createElement("div");
            fileItem.className = "file-item";
            fileItem.innerHTML = `
                <i class="fas fa-${getFileIcon(file.type)}"></i>
                <span>${file.name}</span>
                <button class="remove-file" data-filename="${file.name}">
                    <i class="fas fa-times"></i>
                </button>
            `;
            fileList.appendChild(fileItem);
        });

        fileIndicator.appendChild(fileList);
        fileIndicatorWrapper.appendChild(fileIndicator);

        // Thêm vào trước chat-input-container trong chat-input-wrapper
        const chatInputContainer = document.querySelector(
            ".chat-input-container"
        );
        const chatInputWrapper = document.querySelector(".chat-input-wrapper");
        chatInputWrapper.insertBefore(fileIndicatorWrapper, chatInputContainer);

        // Thêm sự kiện xóa file
        document.querySelectorAll(".remove-file").forEach((btn) => {
            btn.addEventListener("click", function () {
                const filename = this.getAttribute("data-filename");
                // Xóa file khỏi danh sách
                uploadedFiles = uploadedFiles.filter(
                    (file) => file.name !== filename
                );

                // Xóa item hiển thị
                this.closest(".file-item").remove();

                // Nếu không còn file nào, xóa indicator
                if (uploadedFiles.length === 0) {
                    fileIndicatorWrapper.remove();
                }
            });
        });
    }

    // Xác định icon dựa vào loại file
    function getFileIcon(fileType) {
        if (fileType.includes("image")) return "image";
        if (fileType.includes("pdf")) return "file-pdf";
        if (fileType.includes("word") || fileType.includes("doc"))
            return "file-word";
        if (fileType.includes("text") || fileType.includes("txt"))
            return "file-alt";
        return "file";
    }

    // Cập nhật giao diện settings để thêm tùy chọn cài đặt topic
    function updateSettingsPanel() {
        // Thêm section mới vào settings panel
        const settingGroup = document.createElement("div");
        settingGroup.className = "setting-group";
        settingGroup.innerHTML = `
            <h4>Cài đặt API</h4>
            <div class="setting-item">
                <span>Topic</span>
                <input type="text" id="topic-input" value="${currentTopic}" placeholder="Nhập topic">
            </div>
            <button id="save-topic" class="btn-secondary">Lưu cài đặt</button>
        `;

        // Thêm vào panel
        const settingsContent = document.querySelector(".settings-content");

        // Kiểm tra xem đã có section này chưa
        if (!document.getElementById("topic-input")) {
            // Chèn trước phần "Lịch sử"
            const historyGroup = document.querySelector(
                ".setting-group:last-child"
            );
            if (historyGroup) {
                settingsContent.insertBefore(settingGroup, historyGroup);
            } else {
                settingsContent.appendChild(settingGroup);
            }

            // Thêm sự kiện cho nút lưu
            document
                .getElementById("save-topic")
                .addEventListener("click", function () {
                    const newTopic = document
                        .getElementById("topic-input")
                        .value.trim();
                    if (newTopic) {
                        currentTopic = newTopic;
                        localStorage.setItem("chatTopic", newTopic);
                        alert("Đã lưu cài đặt topic!");
                    } else {
                        alert("Topic không được để trống!");
                    }
                });
        }
    }

    // Clear chat
    clearChatBtn.addEventListener("click", function () {
        if (
            confirm(
                "Bạn có chắc muốn xóa tất cả tin nhắn trong cuộc trò chuyện hiện tại?"
            )
        ) {
            // Lấy phiên chat hiện tại
            const activeChat = document.querySelector(
                ".conversation-item.active"
            );
            if (activeChat) {
                // Xóa tất cả tin nhắn và hiển thị welcome screen
                chatMessages.innerHTML = "";
                if (chatWelcome) {
                    chatWelcome.style.display = "block";
                }

                // Xóa tin nhắn trong localStorage
                const chatId = activeChat.getAttribute("data-id");
                const conversations = JSON.parse(
                    localStorage.getItem("conversations") || "[]"
                );
                const chatIndex = conversations.findIndex(
                    (c) => c.id === parseInt(chatId)
                );
                if (chatIndex !== -1) {
                    conversations[chatIndex].messages = [];
                    localStorage.setItem(
                        "conversations",
                        JSON.stringify(conversations)
                    );
                }

                // Reset input
                userInput.value = "";
                resetInputHeight();
            }
        }
    });

    // Khôi phục đánh giá từ localStorage
    function restoreRatings() {
        try {
            const savedRatings = localStorage.getItem("messageRatings");
            if (savedRatings) {
                messageRatings = JSON.parse(savedRatings);
                console.log("Đã khôi phục đánh giá tin nhắn:", messageRatings);
                // Cập nhật hiển thị đánh giá cho các tin nhắn hiện có
                updateRatingDisplay();
            }
        } catch (e) {
            console.error("Lỗi khi khôi phục đánh giá:", e);
            messageRatings = {};
        }
    }

    // Đọc file dưới dạng Base64
    function readFileAsBase64(file) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = () => resolve(reader.result.split(",")[1]);
            reader.onerror = (error) => reject(error);
            reader.readAsDataURL(file);
        });
    }

    // Xử lý nút Think
    if (thinkToggleBtn) {
        thinkToggleBtn.addEventListener("click", function (e) {
            // Tạo hiệu ứng ripple
            const ripple = document.createElement("span");
            ripple.classList.add("ripple");
            this.appendChild(ripple);

            const rect = this.getBoundingClientRect();
            const size = Math.max(rect.width, rect.height);
            ripple.style.width = ripple.style.height = size + "px";
            ripple.style.left = e.clientX - rect.left - size / 2 + "px";
            ripple.style.top = e.clientY - rect.top - size / 2 + "px";

            // Xóa hiệu ứng sau khi hoàn thành animation
            setTimeout(() => {
                ripple.remove();
            }, 600);

            // Thay đổi trạng thái think
            thinkEnabled = !thinkEnabled;
            localStorage.setItem("thinkEnabled", thinkEnabled);
            thinkToggleBtn.classList.toggle("active", thinkEnabled);

            // Thông báo trạng thái
            const toastMessage = thinkEnabled
                ? "Đã bật chế độ Think: AI sẽ hiển thị quá trình suy nghĩ"
                : "Đã tắt chế độ Think: AI sẽ chỉ hiển thị kết quả cuối cùng";
            showToast(toastMessage, thinkEnabled ? "success" : "info");
        });
    }

    function showToast(message, type = "info", duration = 3000) {
        // Kiểm tra xem đã có toast container chưa
        let toastContainer = document.querySelector(".toast-container");

        if (!toastContainer) {
            toastContainer = document.createElement("div");
            toastContainer.className = "toast-container";
            document.body.appendChild(toastContainer);

            // Thêm CSS cho toast container nếu chưa có
            const style = document.createElement("style");
            style.textContent = `
                .toast-container {
                    position: fixed;
                    top: 20px;
                    right: 20px;
                    z-index: 9999;
                }
                .toast {
                    padding: 12px 20px;
                    margin-bottom: 10px;
                    border-radius: 8px;
                    color: white;
                    font-size: 14px;
                    box-shadow: 0 4px 12px rgba(0,0,0,0.2);
                    display: flex;
                    align-items: center;
                    animation: slideIn 0.3s, fadeOut 0.5s ${
                        duration / 1000 - 0.5
                    }s forwards;
                    max-width: 320px;
                    backdrop-filter: blur(10px);
                }
                .toast i {
                    margin-right: 10px;
                    font-size: 16px;
                }
                .toast.success {
                    background-color: rgba(16, 163, 127, 0.95);
                }
                .toast.error {
                    background-color: rgba(244, 67, 54, 0.95);
                }
                .toast.warning {
                    background-color: rgba(255, 152, 0, 0.95);
                }
                .toast.info {
                    background-color: rgba(33, 150, 243, 0.95);
                }
                @keyframes slideIn {
                    from { transform: translateX(100%); opacity: 0; }
                    to { transform: translateX(0); opacity: 1; }
                }
                @keyframes fadeOut {
                    from { opacity: 1; }
                    to { opacity: 0; }
                }
            `;
            document.head.appendChild(style);
        }

        // Tạo toast
        const toast = document.createElement("div");
        toast.className = `toast ${type}`;

        // Icon dựa vào loại toast
        let icon = "info-circle";
        if (type === "success") icon = "check-circle";
        if (type === "error") icon = "exclamation-circle";
        if (type === "warning") icon = "exclamation-triangle";

        toast.innerHTML = `<i class="fas fa-${icon}"></i>${message}`;
        toastContainer.appendChild(toast);

        // Tự động xóa toast sau thời gian định trước
        setTimeout(() => {
            toast.remove();
        }, duration);
    }
});
