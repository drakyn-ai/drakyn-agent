// Get token from cookie
function getTokenFromCookie() {
    const name = 'access_token=';
    const decodedCookie = decodeURIComponent(document.cookie);
    const ca = decodedCookie.split(';');
    for (let i = 0; i < ca.length; i++) {
        let c = ca[i];
        while (c.charAt(0) == ' ') {
            c = c.substring(1);
        }
        if (c.indexOf(name) == 0) {
            return c.substring(name.length, c.length);
        }
    }
    return null;
}

let currentConversationId = null;
let ws = null;
const token = getTokenFromCookie();

// DOM elements
const conversationsList = document.getElementById('conversations-list');
const messagesContainer = document.getElementById('messages-container');
const messageForm = document.getElementById('message-form');
const messageInput = document.getElementById('message-input');
const sendBtn = document.getElementById('send-btn');
const newChatBtn = document.getElementById('new-chat-btn');
const chatTitle = document.getElementById('chat-title');

// Load conversations on page load
loadConversations();

// New chat button
newChatBtn.addEventListener('click', async () => {
    const response = await fetch('/api/conversations', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ title: 'New Conversation' })
    });

    const data = await response.json();
    await loadConversations();
    selectConversation(data.conversation_id);
});

// Message form submission
messageForm.addEventListener('submit', async (e) => {
    e.preventDefault();

    const message = messageInput.value.trim();
    if (!message || !currentConversationId) return;

    // Disable input
    messageInput.disabled = true;
    sendBtn.disabled = true;

    // Send message via WebSocket
    ws.send(JSON.stringify({ message }));

    // Clear input
    messageInput.value = '';
});

// Load conversations
async function loadConversations() {
    const response = await fetch('/api/conversations');
    const data = await response.json();

    conversationsList.innerHTML = '';

    data.conversations.forEach(conv => {
        const div = document.createElement('div');
        div.className = 'conversation-item';
        if (conv.id === currentConversationId) {
            div.classList.add('active');
        }

        const date = new Date(conv.updated_at);
        div.innerHTML = `
            <div class="conversation-title">${conv.title}</div>
            <div class="conversation-date">${formatDate(date)}</div>
        `;

        div.addEventListener('click', () => selectConversation(conv.id));
        conversationsList.appendChild(div);
    });
}

// Select a conversation
async function selectConversation(conversationId) {
    currentConversationId = conversationId;

    // Update UI
    await loadConversations();

    // Close existing WebSocket
    if (ws) {
        ws.close();
    }

    // Clear messages
    messagesContainer.innerHTML = '';

    // Load conversation history
    const response = await fetch(`/api/conversations/${conversationId}`);
    const data = await response.json();

    data.messages.forEach(msg => {
        addMessage(msg.role, msg.content);
    });

    // Connect WebSocket
    connectWebSocket(conversationId);

    // Enable input
    messageInput.disabled = false;
    sendBtn.disabled = false;
    messageInput.focus();

    // Update title
    chatTitle.textContent = 'Chat';
}

// Connect WebSocket
function connectWebSocket(conversationId) {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/chat/${conversationId}`;

    ws = new WebSocket(wsUrl);

    ws.onopen = () => {
        // Send token for authentication
        ws.send(JSON.stringify({ token }));
    };

    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);

        if (data.type === 'user_message') {
            addMessage('user', data.content);
        } else if (data.type === 'start') {
            addTypingIndicator();
        } else if (data.type === 'chunk') {
            appendToLastMessage(data.content);
        } else if (data.type === 'end') {
            removeTypingIndicator();
            messageInput.disabled = false;
            sendBtn.disabled = false;
            messageInput.focus();
        }
    };

    ws.onerror = (error) => {
        console.error('WebSocket error:', error);
    };

    ws.onclose = () => {
        console.log('WebSocket closed');
    };
}

// Add message to chat
function addMessage(role, content) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}`;

    const roleLabel = document.createElement('div');
    roleLabel.className = 'message-role';
    roleLabel.textContent = role === 'user' ? 'You' : 'Assistant';

    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    contentDiv.textContent = content;

    messageDiv.appendChild(roleLabel);
    messageDiv.appendChild(contentDiv);
    messagesContainer.appendChild(messageDiv);

    scrollToBottom();
}

// Add typing indicator
function addTypingIndicator() {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message assistant';
    messageDiv.id = 'typing-indicator';

    const roleLabel = document.createElement('div');
    roleLabel.className = 'message-role';
    roleLabel.textContent = 'Assistant';

    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    contentDiv.id = 'streaming-message';
    contentDiv.textContent = '';

    messageDiv.appendChild(roleLabel);
    messageDiv.appendChild(contentDiv);
    messagesContainer.appendChild(messageDiv);

    scrollToBottom();
}

// Append to last message (streaming)
function appendToLastMessage(chunk) {
    const streamingMsg = document.getElementById('streaming-message');
    if (streamingMsg) {
        streamingMsg.textContent += chunk;
        scrollToBottom();
    }
}

// Remove typing indicator
function removeTypingIndicator() {
    const indicator = document.getElementById('typing-indicator');
    if (indicator) {
        indicator.id = '';
        const content = document.getElementById('streaming-message');
        if (content) {
            content.id = '';
        }
    }
}

// Scroll to bottom
function scrollToBottom() {
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

// Format date
function formatDate(date) {
    const now = new Date();
    const diff = now - date;
    const days = Math.floor(diff / (1000 * 60 * 60 * 24));

    if (days === 0) {
        return 'Today';
    } else if (days === 1) {
        return 'Yesterday';
    } else if (days < 7) {
        return `${days} days ago`;
    } else {
        return date.toLocaleDateString();
    }
}

// Handle Enter key (Shift+Enter for new line)
messageInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        messageForm.dispatchEvent(new Event('submit'));
    }
});
