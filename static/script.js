const chatForm = document.getElementById("chatForm");
const messageInput = document.getElementById("messageInput");
const sendButton = document.getElementById("sendButton");
const chatArea = document.querySelector(".chat-area");

let conversation = [];
let isSending = false;

function addMessage(text, role) {
    const message = document.createElement("div");
    message.className = `message ${role}`;
    message.textContent = text;
    chatArea.appendChild(message);
    chatArea.scrollTop = chatArea.scrollHeight;
    return message;
}

function newChat() {
    conversation = [];
    chatArea.innerHTML = `
        <div class="welcome">
            <div class="welcome-logo">C</div>
            <h1>Welcome to CHAMBO AI</h1>
            <p class="welcome-small">Your AI assistant</p>
            <p class="description">
                Ask anything. Learn, create and explore with CHAMBO AI.
            </p>
            <div class="suggestions">
                <button onclick="useSuggestion('Explain artificial intelligence simply')">Explain AI</button>
                <button onclick="useSuggestion('Give me a simple Python program')">Coding help</button>
                <button onclick="useSuggestion('Teach me English speaking')">Learn English</button>
                <button onclick="useSuggestion('Tell me an interesting fact')">Interesting facts</button>
            </div>
        </div>
    `;
    messageInput.value = "";
}

function useSuggestion(text) {
    messageInput.value = text;
    sendMessage();
}

async function sendMessage() {
    const text = messageInput.value.trim();

    if (!text || isSending) return;

    isSending = true;
    sendButton.disabled = true;

    const welcome = chatArea.querySelector(".welcome");
    if (welcome) welcome.remove();

    addMessage(text, "user");
    messageInput.value = "";

    const loading = addMessage("CHAMBO AI is thinking...", "assistant");

    try {
        const response = await fetch("/api/chat", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                message: text,
                history: conversation
            })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || "Something went wrong.");
        }

        loading.textContent = data.reply || "No response received.";

        conversation.push(
            { role: "user", content: text },
            { role: "assistant", content: data.reply }
        );

    } catch (error) {
        loading.textContent = "Error: " + error.message;
    } finally {
        isSending = false;
        sendButton.disabled = false;
        messageInput.focus();
    }
}

chatForm.addEventListener("submit", function(event) {
    event.preventDefault();
    sendMessage();
});

messageInput.addEventListener("keydown", function(event) {
    if (event.key === "Enter" && !event.shiftKey) {
        event.preventDefault();
        sendMessage();
    }
});