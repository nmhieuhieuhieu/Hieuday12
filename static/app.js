document.addEventListener('DOMContentLoaded', () => {
    const chatForm = document.getElementById('chatForm');
    const userInput = document.getElementById('userInput');
    const chatBox = document.getElementById('chatBox');
    const apiKeyInput = document.getElementById('apiKey');
    const healthStatus = document.getElementById('healthStatus');
    const statusDot = document.querySelector('.status-dot');

    // Lọc input key
    const getApiKey = () => apiKeyInput.value.trim();

    // Sinh HTML Message
    const createMessageElement = (content, isUser = false) => {
        const wrapper = document.createElement('div');
        wrapper.className = `message ${isUser ? 'user-message' : 'ai-message'}`;
        
        const avatar = document.createElement('div');
        avatar.className = 'avatar';
        avatar.textContent = isUser ? 'ME' : 'AI';

        const contentDiv = document.createElement('div');
        contentDiv.className = 'content';
        contentDiv.textContent = content; // prevents XSS

        wrapper.appendChild(avatar);
        wrapper.appendChild(contentDiv);
        return wrapper;
    };

    const addTypingIndicator = () => {
        const wrapper = document.createElement('div');
        wrapper.className = 'message ai-message typing-wrap';
        wrapper.id = 'typingIndicator';
        
        const avatar = document.createElement('div');
        avatar.className = 'avatar';
        avatar.textContent = 'AI';

        const contentDiv = document.createElement('div');
        contentDiv.className = 'content';
        contentDiv.innerHTML = `
            <div class="typing-indicator">
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
            </div>
        `;

        wrapper.appendChild(avatar);
        wrapper.appendChild(contentDiv);
        chatBox.appendChild(wrapper);
        chatBox.scrollTop = chatBox.scrollHeight;
    };

    const removeTypingIndicator = () => {
        const ind = document.getElementById('typingIndicator');
        if (ind) ind.remove();
    };

    // Kiểm tra Health Server
    const checkServerHealth = async () => {
        try {
            const res = await fetch('/health');
            if (res.ok) {
                healthStatus.textContent = "Online - Ready";
                statusDot.className = "status-dot healthy";
            } else {
                healthStatus.textContent = "Offline / Errors";
                statusDot.className = "status-dot error";
            }
        } catch (e) {
            healthStatus.textContent = "Connection Refused";
            statusDot.className = "status-dot error";
        }
    };

    // Initial check
    checkServerHealth();
    setInterval(checkServerHealth, 30000); // Check every 30s

    // Gửi tin nhắn
    chatForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const text = userInput.value.trim();
        const key = getApiKey();
        
        if (!text) return;
        if (!key) {
            alert("Vui lòng nhập API Key ở menu Settings bên trái");
            apiKeyInput.focus();
            return;
        }

        // Add User Message
        chatBox.appendChild(createMessageElement(text, true));
        userInput.value = '';
        chatBox.scrollTop = chatBox.scrollHeight;

        // Show typing
        addTypingIndicator();

        try {
            // Cổng API Backend
            const targetUrl = window.location.origin + '/ask';
            
            const response = await fetch(targetUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-API-Key': key
                },
                body: JSON.stringify({ question: text })
            });

            removeTypingIndicator();

            if (response.status === 429) {
                chatBox.appendChild(createMessageElement("⚠️ Bạn đã gửi quá nhiều tin nhắn (Rate Limit Exceeded). Hãy đợi một lát rồi thử lại nhé.", false));
            } else if (response.status === 401) {
                chatBox.appendChild(createMessageElement("⚠️ API Key của bạn bị từ chối. Vui lòng kiểm tra lại.", false));
                apiKeyInput.classList.add('error');
            } else if (!response.ok) {
                chatBox.appendChild(createMessageElement("⚠️ Lỗi rùi! Server trả về mã: " + response.status, false));
            } else {
                const data = await response.json();
                chatBox.appendChild(createMessageElement(data.answer, false));
            }
            
        } catch (error) {
            removeTypingIndicator();
            console.error("Fetch error:", error);
            chatBox.appendChild(createMessageElement("⚠️ Lỗi mất mạng: Không thể kết nối tới Backend.", false));
        }

        chatBox.scrollTop = chatBox.scrollHeight;
    });
});
