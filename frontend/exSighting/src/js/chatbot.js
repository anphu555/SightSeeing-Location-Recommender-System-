async function sendMessage() {
    const inputField = document.getElementById("user-input");
    const chatBox = document.getElementById("chat-box");
    const message = inputField.value.trim();

    if (!message) return;

    // 1. Add User Message to Chat
    addMessage(message, "user-message");
    inputField.value = ""; // Clear input

    // 2. Show "Typing..." indicator (Optional but good UX)
    const loadingId = "loading-" + Date.now();
    addMessage("Typing...", "bot-message", loadingId);

    try {
        // 3. Send Request to FastAPI Backend
        const response = await fetch("http://127.0.0.1:8000/chat", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ message: message })
        });

        const data = await response.json();

        // 4. Remove Loading Text and Add Bot Response
        removeMessage(loadingId);
        addMessage(data.reply, "bot-message");

    } catch (error) {
        console.error("Error:", error);
        removeMessage(loadingId);
        addMessage("Sorry, something went wrong.", "bot-message");
    }
}

// Helper to add a message bubble to the chat box
function addMessage(text, className, id = null) {
    const chatBox = document.getElementById("chat-box");
    const msgDiv = document.createElement("div");
    msgDiv.classList.add("message", className);
    msgDiv.innerText = text;
    if (id) msgDiv.id = id;
    
    chatBox.appendChild(msgDiv);
    chatBox.scrollTop = chatBox.scrollHeight; // Auto-scroll to bottom
}

// Helper to remove a specific message (used for loading state)
function removeMessage(id) {
    const element = document.getElementById(id);
    if (element) element.remove();
}

// Allow sending message with "Enter" key
document.getElementById("user-input").addEventListener("keypress", function (e) {
    if (e.key === "Enter") sendMessage();
});