window.onload = function () {

    const sendBtn = document.getElementById("send-btn");
    const messageInput = document.getElementById("message-input");
    const chatBox = document.getElementById("chat-box");

    sendBtn.onclick = async function () {

        const message = messageInput.value;

        // Prevent empty messages
        if (message.trim() === "") {
            return;
        }

        // Display user message
        chatBox.innerHTML += `
            <p><strong>You:</strong> ${message}</p>
        `;

        try {

            // Send message to FastAPI
            const response = await fetch(
                "http://127.0.0.1:8000/chat",
                {
                    method: "POST",

                    headers: {
                        "Content-Type": "application/json"
                    },

                    body: JSON.stringify({
                        message: message
                    })
                }
            );

            // Convert response to JSON
            const data = await response.json();

            // Display bot response
            chatBox.innerHTML += `
                <p><strong>Bot:</strong> ${data.response}</p>
            `;

        } catch (error) {

            console.error(error);

            chatBox.innerHTML += `
                <p><strong>Bot:</strong> Error connecting to server.</p>
            `;
        }

        // Clear input box
        messageInput.value = "";

        // Auto-scroll to latest message
        chatBox.scrollTop = chatBox.scrollHeight;
    };

};