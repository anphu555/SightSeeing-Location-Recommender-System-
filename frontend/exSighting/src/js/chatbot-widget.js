import { CONFIG } from './config.js';

class ChatbotWidget {
    constructor() {
        this.isOpen = false;
        this.messages = [];
        this.init();
    }

    init() {
        this.createWidget();
        this.attachEventListeners();
        this.addWelcomeMessage();
    }

    createWidget() {
        const widgetHTML = `
            <div class="chatbot-widget">
                <button class="chatbot-toggle" id="chatbotToggle">
                    <i class="fas fa-comments"></i>
                </button>
                
                <div class="chatbot-window" id="chatbotWindow">
                    <div class="chatbot-header">
                        <div class="chatbot-avatar">
                            <i class="fas fa-robot"></i>
                        </div>
                        <div class="chatbot-info">
                            <h3>Travel Assistant</h3>
                            <p>Online • Ready to help</p>
                        </div>
                        <button class="chatbot-close" id="chatbotClose">
                            <i class="fas fa-times"></i>
                        </button>
                    </div>
                    
                    <div class="chatbot-messages" id="chatbotMessages">
                        <!-- Messages will be inserted here -->
                    </div>
                    
                    <div class="typing-indicator" id="typingIndicator">
                        <div class="message-avatar">
                            <i class="fas fa-robot"></i>
                        </div>
                        <div class="typing-dots">
                            <span></span>
                            <span></span>
                            <span></span>
                        </div>
                    </div>
                    
                    <div class="chatbot-input">
                        <input 
                            type="text" 
                            id="chatbotInput" 
                            placeholder="Type your message..."
                            autocomplete="off"
                        />
                        <button id="chatbotSend">
                            <i class="fas fa-paper-plane"></i>
                        </button>
                    </div>
                </div>
            </div>
        `;

        document.body.insertAdjacentHTML('beforeend', widgetHTML);
    }

    attachEventListeners() {
        const toggle = document.getElementById('chatbotToggle');
        const close = document.getElementById('chatbotClose');
        const send = document.getElementById('chatbotSend');
        const input = document.getElementById('chatbotInput');

        toggle.addEventListener('click', () => this.toggleChat());
        close.addEventListener('click', () => this.toggleChat());
        send.addEventListener('click', () => this.sendMessage());
        
        input.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.sendMessage();
            }
        });
    }

    toggleChat() {
        this.isOpen = !this.isOpen;
        const window = document.getElementById('chatbotWindow');
        const toggle = document.getElementById('chatbotToggle');
        
        if (this.isOpen) {
            window.classList.add('active');
            toggle.classList.add('active');
            toggle.innerHTML = '<i class="fas fa-times"></i>';
        } else {
            window.classList.remove('active');
            toggle.classList.remove('active');
            toggle.innerHTML = '<i class="fas fa-comments"></i>';
        }
    }

    addWelcomeMessage() {
        const welcomeMsg = {
            text: "Hello! 👋 I'm your travel assistant. How can I help you discover amazing places in Vietnam today?",
            isBot: true,
            time: this.getCurrentTime()
        };
        this.addMessage(welcomeMsg);
    }

    async sendMessage() {
        const input = document.getElementById('chatbotInput');
        const message = input.value.trim();
        
        if (!message) return;

        // Add user message
        this.addMessage({
            text: message,
            isBot: false,
            time: this.getCurrentTime()
        });

        input.value = '';
        
        // Show typing indicator
        this.showTyping(true);

        try {
            // Call chatbot API
            const token = localStorage.getItem('token');
            const response = await fetch(`${CONFIG.apiBase}/api/v1/chatbot/chat`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    ...(token && { 'Authorization': `Bearer ${token}` })
                },
                body: JSON.stringify({ message: message })
            });

            if (!response.ok) {
                throw new Error('Failed to get response');
            }

            const data = await response.json();
            
            // Hide typing indicator
            this.showTyping(false);
            
            // Add bot response
            this.addMessage({
                text: data.response || "I'm sorry, I couldn't process that. Can you try again?",
                isBot: true,
                time: this.getCurrentTime()
            });

        } catch (error) {
            console.error('Chatbot error:', error);
            this.showTyping(false);
            
            this.addMessage({
                text: "Sorry, I'm having trouble connecting. Please try again later.",
                isBot: true,
                time: this.getCurrentTime()
            });
        }
    }

    addMessage(message) {
        const messagesContainer = document.getElementById('chatbotMessages');
        const messageHTML = `
            <div class="chat-message ${message.isBot ? 'bot' : 'user'}">
                <div class="message-avatar">
                    <i class="fas fa-${message.isBot ? 'robot' : 'user'}"></i>
                </div>
                <div>
                    <div class="message-content">${this.escapeHtml(message.text)}</div>
                    <div class="message-time">${message.time}</div>
                </div>
            </div>
        `;
        
        messagesContainer.insertAdjacentHTML('beforeend', messageHTML);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
        
        this.messages.push(message);
    }

    showTyping(show) {
        const typingIndicator = document.getElementById('typingIndicator');
        const messagesContainer = document.getElementById('chatbotMessages');
        
        if (show) {
            typingIndicator.classList.add('active');
        } else {
            typingIndicator.classList.remove('active');
        }
        
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    getCurrentTime() {
        const now = new Date();
        return now.toLocaleTimeString('en-US', { 
            hour: '2-digit', 
            minute: '2-digit',
            hour12: false 
        });
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Initialize chatbot when DOM is loaded or immediately if already loaded
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        new ChatbotWidget();
    });
} else {
    // DOM already loaded
    new ChatbotWidget();
}

export default ChatbotWidget;
