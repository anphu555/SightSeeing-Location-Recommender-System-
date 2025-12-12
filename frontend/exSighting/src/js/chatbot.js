async function sendMessage() {
    const inputField = document.getElementById("user-input");
    const message = inputField.value.trim();

    if (!message) return;

    // 1. Hiển thị tin nhắn User
    addMessage(message, "user-message");
    inputField.value = ""; // Xóa ô nhập

    // 2. Hiển thị trạng thái "Đang gõ..."
    const loadingId = "loading-" + Date.now();
    addMessage("Answering...", "bot-message", loadingId);

    try {
        // 3. Gửi Request xuống Backend
        // QUAN TRỌNG: Thêm dấu / vào cuối đường dẫn để khớp với FastAPI
        const response = await fetch("http://127.0.0.1:8000/chat/", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ message: message })
        });

        if (!response.ok) {
            throw new Error("Server or connection error.");
        }

        const data = await response.json();

        // 4. Xóa loading và hiện tin nhắn Bot
        removeMessage(loadingId);
        addMessage(data.reply, "bot-message");

    } catch (error) {
        console.error("Error:", error);
        removeMessage(loadingId);
        addMessage("Sorry, the server is experiencing an issue.", "bot-message");
    }
}

// Hàm hỗ trợ thêm tin nhắn vào khung chat
function addMessage(text, className, id = null) {
    const chatBox = document.getElementById("chat-box");
    const msgDiv = document.createElement("div");
    msgDiv.classList.add("message", className);
    
    if (id) msgDiv.id = id;

    // QUAN TRỌNG: Xử lý hiển thị xuống dòng và in đậm từ Gemini
    // Chuyển \n thành <br>
    // Chuyển **text** thành <b>text</b>
    if (className === "bot-message" && !id) {
         let formattedText = text.replace(/\n/g, "<br>");
         formattedText = formattedText.replace(/\*\*(.*?)\*\*/g, "<b>$1</b>");
         msgDiv.innerHTML = formattedText;
    } else {
        msgDiv.innerText = text; // User message hoặc loading thì giữ nguyên
    }
    
    chatBox.appendChild(msgDiv);
    chatBox.scrollTop = chatBox.scrollHeight; // Tự động cuộn xuống cuối
}

// Hàm xóa tin nhắn (dùng cho loading)
function removeMessage(id) {
    const element = document.getElementById(id);
    if (element) element.remove();
}

// Bắt sự kiện phím Enter
document.getElementById("user-input").addEventListener("keypress", function (e) {
    if (e.key === "Enter") {
        e.preventDefault(); // Ngăn xuống dòng trong ô input
        sendMessage();
    }
});

function toggleChat() {
            const window = document.getElementById("chatWindow");
            const tooltip = document.getElementById("chatTooltip");
            const btn = document.getElementById("chatButton");

            if (window.classList.contains("active")) {
                // Đang mở -> Đóng
                window.classList.remove("active");
                tooltip.classList.remove("hide-tooltip");
                btn.classList.remove("opened");
                btn.innerHTML = '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path></svg>';
            } else {
                // Đang đóng -> Mở
                window.classList.add("active");
                tooltip.classList.add("hide-tooltip");
                btn.classList.add("opened");
                btn.innerHTML = '<span style="color:white; font-size: 24px;">✕</span>';
            }
        }