window.onload = function () {

    // UI Elements
    const launcherBtn = document.getElementById("chat-launcher");
    const chatContainer = document.getElementById("chat-container");
    const closeBtn = document.getElementById("close-chat");
    
    const sendBtn = document.getElementById("send-btn");
    const messageInput = document.getElementById("message-input");
    const chatBox = document.getElementById("chat-box");

    // --- Markdown to HTML Parser ---
    function parseMarkdown(text) {
        // Escape HTML to prevent XSS
        let escaped = text
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;");

        // Convert [Text](URL) markdown links to HTML anchors
        escaped = escaped.replace(/\[([^\]]+)\]\(([^)]+)\)/g, (match, linkText, url) => {
            return `<a href="${url}" target="_blank" class="product-link">${linkText}</a>`;
        });

        // Convert **text** to bold
        escaped = escaped.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');

        // Parse list items (lines starting with •, * or -)
        const lines = escaped.split('\n');
        let inList = false;
        const processedLines = [];

        for (let line of lines) {
            const trimmed = line.trim();
            const isBullet = trimmed.startsWith('•') || trimmed.startsWith('*') || trimmed.startsWith('-');
            
            if (isBullet) {
                if (!inList) {
                    processedLines.push('<ul>');
                    inList = true;
                }
                const itemContent = trimmed.replace(/^[•*\-]\s*/, '');
                processedLines.push(`<li>${itemContent}</li>`);
            } else {
                if (inList) {
                    processedLines.push('</ul>');
                    inList = false;
                }
                processedLines.push(line);
            }
        }
        if (inList) {
            processedLines.push('</ul>');
        }

        let result = processedLines.join('\n');
        result = result
            .replace(/\n<\/ul>/g, '</ul>')
            .replace(/<ul>\n/g, '<ul>')
            .replace(/<\/li>\n<li>/g, '</li><li>')
            .replace(/<\/li>\n/g, '</li>')
            .replace(/\n/g, '<br>');
        
        return result;
    }

    // --- Helper to Append Bot Messages with Quick Actions ---
    function appendBotMessage(text) {
        const formattedResponse = parseMarkdown(text);
        
        const messageWrapper = document.createElement("div");
        messageWrapper.className = "message-wrapper bot-wrapper";

        const messageBubble = document.createElement("div");
        messageBubble.className = "message bot-msg";
        messageBubble.innerHTML = formattedResponse;
        messageWrapper.appendChild(messageBubble);

        const quickActions = document.createElement("div");
        quickActions.className = "quick-actions-container";

        const emailChip = document.createElement("button");
        emailChip.className = "action-chip";
        emailChip.innerHTML = "✉️ Email Us";
        emailChip.onclick = function() {
            messageInput.value = "How can I contact Elactree via email?";
            handleSend();
        };

        const phoneChip = document.createElement("button");
        phoneChip.className = "action-chip";
        phoneChip.innerHTML = "📞 Call Us";
        phoneChip.onclick = function() {
            messageInput.value = "How can I contact Elactree via phone?";
            handleSend();
        };

        quickActions.appendChild(emailChip);
        quickActions.appendChild(phoneChip);
        messageWrapper.appendChild(quickActions);

        chatBox.appendChild(messageWrapper);
        chatBox.scrollTop = chatBox.scrollHeight;
    }

    // --- Helper to Append Error Message ---
    function appendErrorMessage(text) {
        const messageWrapper = document.createElement("div");
        messageWrapper.className = "message-wrapper bot-wrapper";

        const messageBubble = document.createElement("div");
        messageBubble.className = "message bot-msg";
        messageBubble.style.color = "#DC2626";
        messageBubble.style.border = "1px solid #FECACA";
        messageBubble.style.backgroundColor = "#FEF2F2";
        messageBubble.textContent = text;
        messageWrapper.appendChild(messageBubble);

        chatBox.appendChild(messageWrapper);
        chatBox.scrollTop = chatBox.scrollHeight;
    }

    // --- Welcome Message ---
    appendBotMessage("Hello! Welcome to Elactree. I am your AI sales assistant.\n\nFeel free to ask me about our active LEDs, interactive flat panels, commercial TVs, cameras, or audio equipment!");

    // --- Widget Open/Close Logic ---
    launcherBtn.onclick = function() {
        chatContainer.classList.remove("hidden");
        launcherBtn.style.display = "none"; // Hide launcher icon when open
        messageInput.focus();
    };

    closeBtn.onclick = function() {
        chatContainer.classList.add("hidden");
        launcherBtn.style.display = "flex"; // Show launcher icon when closed
    };

    // --- Chat Submit Handler ---
    async function handleSend() {
        const message = messageInput.value;

        if (message.trim() === "") return;

        // Disable inputs during network request
        sendBtn.disabled = true;
        messageInput.disabled = true;

        // Append user message securely (using textContent via DOM node to avoid XSS)
        const userWrapper = document.createElement("div");
        userWrapper.className = "message-wrapper user-wrapper";
        const userBubble = document.createElement("div");
        userBubble.className = "message user-msg";
        userBubble.textContent = message;
        userWrapper.appendChild(userBubble);
        
        chatBox.appendChild(userWrapper);
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

            appendBotMessage(data.response);

        } catch (error) {
            console.error("Chat Error:", error);
            appendErrorMessage(`Error: ${error.message}`);
        } finally {
            // Re-enable inputs
            sendBtn.disabled = false;
            messageInput.disabled = false;
            messageInput.focus();
            chatBox.scrollTop = chatBox.scrollHeight;
        }
    }

    sendBtn.onclick = handleSend;

    messageInput.addEventListener("keypress", function (event) {
        if (event.key === "Enter") {
            event.preventDefault();
            handleSend();
        }
    });
};