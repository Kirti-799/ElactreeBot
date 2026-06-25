window.onload = function () {

    // UI Elements
    const launcherBtn = document.getElementById("chat-launcher");
    const chatContainer = document.getElementById("chat-container");
    const closeBtn = document.getElementById("close-chat");
    
    const sendBtn = document.getElementById("send-btn");
    const messageInput = document.getElementById("message-input");
    const chatBox = document.getElementById("chat-box");

    // --- Widget Open/Close Logic ---
    launcherBtn.onclick = function() {
        chatContainer.classList.remove("hidden");
        launcherBtn.style.display = "none"; // Hide icon when open
        messageInput.focus();
    };

    closeBtn.onclick = function() {
        chatContainer.classList.add("hidden");
        launcherBtn.style.display = "flex"; // Show icon when closed
    };

    // --- Chat Logic ---
    messageInput.addEventListener("keypress", function (event) {
        if (event.key === "Enter") {
            event.preventDefault();
            sendBtn.click();
        }
    });

    sendBtn.onclick = async function () {
        const message = messageInput.value;

        if (message.trim() === "") return;

        // Disable inputs to prevent spamming the rate limit
        sendBtn.disabled = true;
        messageInput.disabled = true;
        sendBtn.innerText = "...";

        // Display user message WITHOUT the "You:" label
        chatBox.innerHTML += `
            <div class="message user-msg">
                ${message}
            </div>
        `;

        messageInput.value = "";
        chatBox.scrollTop = chatBox.scrollHeight;

        try {
            const response = await fetch("http://127.0.0.1:8000/chat", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ message: message })
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.detail || "Server error.");
            }

            const formattedResponse = data.response.replace(/\n/g, "<br>");

            // Display bot message WITHOUT the "Bot:" label
            chatBox.innerHTML += `
                <div class="message bot-msg">
                    ${formattedResponse}
                </div>
            `;

        } catch (error) {
            console.error("Chat Error:", error);
            chatBox.innerHTML += `
                <div class="message bot-msg" style="color: #dc3545; border: 1px solid #dc3545;">
                    ${error.message}
                </div>
            `;
        } finally {
            // Re-enable inputs
            sendBtn.disabled = false;
            messageInput.disabled = false;
            sendBtn.innerText = "Send";
            messageInput.focus();
            chatBox.scrollTop = chatBox.scrollHeight;
        }
    };
};