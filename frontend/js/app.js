import { requireAuth, initLogout, isAuthenticated } from './auth.js';
import { chatAPI, memoryAPI } from './api.js';

// Main App Class
class ChatApp {
    constructor() {
        this.currentSessionId = null;
        this.sessions = [];
        this.messages = [];
        this.isLoading = false;
        this.memoryEnabled = true;
        this.currentModel = 'x-ai/grok-3-mini-beta';
        
        this.init();
    }
    
    async init() {
        // Check authentication
        // Check authentication
    if (!isAuthenticated()) {
        window.location.href = '/login.html';
        return;
    }
    
    // Load user data
    await this.loadUserProfile();
    await this.loadSessions();
        requireAuth();
        
        // Load user data
        await this.loadUserProfile();
        await this.loadSessions();
        
        // Setup event listeners
        this.setupEventListeners();
        
        // Check for session in URL
        const urlParams = new URLSearchParams(window.location.search);
        const sessionId = urlParams.get('session');
        if (sessionId) {
            await this.loadSession(parseInt(sessionId));
        }
    }
    
    setupEventListeners() {
    console.log('Setting up event listeners');
    
    // New chat button
    const newChatBtn = document.getElementById('newChatBtn');
    if (newChatBtn) {
        newChatBtn.addEventListener('click', () => {
            console.log('New chat clicked');
            this.newChat();
        });
    } else {
        console.log('New chat button not found');
    }
    
    // Send button
    const sendBtn = document.getElementById('sendBtn');
    const messageInput = document.getElementById('messageInput');
    
    if (sendBtn) {
        console.log('Send button found, attaching click handler');
        sendBtn.onclick = () => {  // Use onclick instead of addEventListener to ensure it works
            console.log('Send button clicked');
            this.sendMessage();
        };
    } else {
        console.log('Send button not found');
    }
    
    // Enter key handler
    if (messageInput) {
        console.log('Message input found');
        messageInput.onkeydown = (e) => {  // Use onkeydown instead of addEventListener
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                console.log('Enter pressed');
                this.sendMessage();
            }
        };
        
        // Auto-resize
        messageInput.oninput = function() {
            this.style.height = 'auto';
            this.style.height = (this.scrollHeight) + 'px';
        };
    } else {
        console.log('Message input not found');
    }
    
    // Memory toggle
    const memoryToggle = document.getElementById('memoryToggle');
    if (memoryToggle) {
        memoryToggle.onchange = (e) => {
            this.memoryEnabled = e.target.checked;
            this.updateMemoryIndicator();
        };
    }
    
    // Model selector
    const modelSelect = document.getElementById('modelSelect');
    if (modelSelect) {
        modelSelect.onchange = (e) => {
            this.currentModel = e.target.value;
        };
    }
    
    console.log('Event listeners setup complete');
    
    // Auto-resize textarea
    if (messageInput) {
        messageInput.addEventListener('input', function() {
            this.style.height = 'auto';
            this.style.height = (this.scrollHeight) + 'px';
        });
    }
}
    
    async loadUserProfile() {
        const username = localStorage.getItem('username');
        if (username) {
            document.getElementById('username').textContent = username;
            document.getElementById('userInitials').textContent = username.charAt(0).toUpperCase();
        }
    }
    
    async loadSessions() {
        try {
            this.sessions = await chatAPI.getSessions();
            this.renderSessions();
        } catch (error) {
            console.error('Failed to load sessions:', error);
        }
    }
    
    renderSessions() {
        const container = document.getElementById('conversationsList');
        
        if (this.sessions.length === 0) {
            container.innerHTML = '<p class="text-secondary">No conversations yet</p>';
            return;
        }
        
        container.innerHTML = this.sessions.map(session => `
            <div class="conversation-item ${session.id === this.currentSessionId ? 'active' : ''}" 
                 data-session-id="${session.id}">
                <div class="conversation-title">${this.escapeHtml(session.title)}</div>
                <div class="conversation-date">${new Date(session.created_at).toLocaleDateString()}</div>
                <button class="delete-conversation" data-session-id="${session.id}">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                        <path d="M18 6L6 18M6 6l12 12"/>
                    </svg>
                </button>
            </div>
        `).join('');
        
        // Add click handlers
        container.querySelectorAll('.conversation-item').forEach(item => {
            item.addEventListener('click', (e) => {
                if (!e.target.closest('.delete-conversation')) {
                    const sessionId = item.dataset.sessionId;
                    this.loadSession(parseInt(sessionId));
                }
            });
        });
        
        // Add delete handlers
        container.querySelectorAll('.delete-conversation').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const sessionId = btn.dataset.sessionId;
                this.deleteSession(parseInt(sessionId));
            });
        });
    }
    
    async loadSession(sessionId) {
        try {
            this.currentSessionId = sessionId;
            this.messages = await chatAPI.getSessionMessages(sessionId);
            this.renderMessages();
            
            // Update URL
            const url = new URL(window.location);
            url.searchParams.set('session', sessionId);
            window.history.pushState({}, '', url);
            
            // Update active state in sidebar
            this.renderSessions();
            
            // Update header
            const session = this.sessions.find(s => s.id === sessionId);
            if (session) {
                document.getElementById('currentSessionTitle').textContent = session.title;
                this.memoryEnabled = session.memory_enabled;
                document.getElementById('memoryToggle').checked = this.memoryEnabled;
                this.updateMemoryIndicator();
            }
        } catch (error) {
            console.error('Failed to load session:', error);
        }
    }
    
    async newChat() {
        this.currentSessionId = null;
        this.messages = [];
        this.renderMessages();
        
        document.getElementById('currentSessionTitle').textContent = 'New Chat';
        
        // Remove session from URL
        const url = new URL(window.location);
        url.searchParams.delete('session');
        window.history.pushState({}, '', url);
        
        // Show welcome message
        document.getElementById('welcomeMessage').classList.remove('hidden');
    }
    
    async deleteSession(sessionId) {
        if (!confirm('Are you sure you want to delete this conversation?')) {
            return;
        }
        
        try {
            await chatAPI.deleteSession(sessionId);
            
            if (this.currentSessionId === sessionId) {
                this.newChat();
            }
            
            await this.loadSessions();
        } catch (error) {
            console.error('Failed to delete session:', error);
        }
    }
    
    async sendMessage() {
    console.log('sendMessage called');
    const input = document.getElementById('messageInput');
    const message = input.value.trim();
    
    console.log('Message:', message);
    
    if (!message || this.isLoading) {
        console.log('No message or loading');
        return;
    }
    
    // Hide welcome message
    document.getElementById('welcomeMessage').classList.add('hidden');
    
    // Add user message to UI
    this.addMessageToUI('user', message);
    
    // Clear input
    input.value = '';
    input.style.height = 'auto';
    
    // Show typing indicator
    this.showTypingIndicator();
    
    this.isLoading = true;
    this.updateSendButton();
    
    try {
        console.log('Sending message to API...');
        // Get selected model
        const modelSelect = document.getElementById('modelSelect');
        const selectedModel = modelSelect ? modelSelect.value : 'x-ai/grok-3-mini-beta';
        
        const response = await chatAPI.sendMessage(
            message, 
            this.currentSessionId,
            this.memoryEnabled,
            { model: selectedModel }
        );
        
        console.log('API response:', response);
        
        // Remove typing indicator
        this.hideTypingIndicator();
        
        // Add AI response to UI
        this.addMessageToUI('assistant', response.message);
        
        // Update session info
        if (!this.currentSessionId) {
            this.currentSessionId = response.session_id;
            await this.loadSessions();
        }
        
    } catch (error) {
        console.error('Failed to send message:', error);
        this.hideTypingIndicator();
        this.showError('Failed to send message. Please try again.');
    } finally {
        this.isLoading = false;
        this.updateSendButton();
    }
}
    
    addMessageToUI(role, content) {
        const container = document.getElementById('messagesContainer');
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${role}`;
        
        const avatar = role === 'user' 
            ? localStorage.getItem('username')?.charAt(0).toUpperCase() || 'U'
            : 'AI';
        
        messageDiv.innerHTML = `
            <div class="message-avatar">${avatar}</div>
            <div class="message-content">
                <div class="message-text">${this.formatMessage(content)}</div>
                <div class="message-actions">
                    <button class="copy-message" title="Copy message">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                            <rect x="9" y="9" width="13" height="13" rx="2" ry="2"/>
                            <path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"/>
                        </svg>
                    </button>
                </div>
            </div>
        `;
        
        container.appendChild(messageDiv);
        
        // Add copy handler
        messageDiv.querySelector('.copy-message')?.addEventListener('click', () => {
            navigator.clipboard.writeText(content);
            this.showToast('Message copied to clipboard');
        });
        
        // Scroll to bottom
        this.scrollToBottom();
    }
    
    formatMessage(content) {
        return content
            .replace(/\n/g, '<br>')
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/`(.*?)`/g, '<code>$1</code>');
    }
    
    showTypingIndicator() {
        const container = document.getElementById('messagesContainer');
        const indicator = document.createElement('div');
        indicator.className = 'typing-indicator';
        indicator.id = 'typingIndicator';
        indicator.innerHTML = '<span></span><span></span><span></span>';
        container.appendChild(indicator);
        this.scrollToBottom();
    }
    
    hideTypingIndicator() {
        const indicator = document.getElementById('typingIndicator');
        if (indicator) {
            indicator.remove();
        }
    }
    
    renderMessages() {
        const container = document.getElementById('messagesContainer');
        container.innerHTML = '';
        
        if (this.messages.length === 0) {
            document.getElementById('welcomeMessage').classList.remove('hidden');
            return;
        }
        
        document.getElementById('welcomeMessage').classList.add('hidden');
        
        this.messages.forEach(message => {
            this.addMessageToUI(message.role, message.content);
        });
    }
    
    async loadPreferences() {
        try {
            const data = await memoryAPI.getPreferences();
            this.renderPreferences(data.preferences);
        } catch (error) {
            console.error('Failed to load preferences:', error);
        }
    }
    
    renderPreferences(preferences) {
        const container = document.getElementById('preferencesList');
        if (!container) return;
        
        if (!preferences || Object.keys(preferences).length === 0) {
            container.innerHTML = '<p class="text-secondary">No preferences detected yet</p>';
            return;
        }
        
        container.innerHTML = '';
        for (const [key, values] of Object.entries(preferences)) {
            if (Array.isArray(values) && values.length > 0) {
                const categoryDiv = document.createElement('div');
                categoryDiv.className = 'preference-category';
                categoryDiv.innerHTML = `<h5>${this.capitalize(key)}</h5>`;
                values.forEach(value => {
                    categoryDiv.innerHTML += `<div class="preference-item">${this.escapeHtml(value)}</div>`;
                });
                container.appendChild(categoryDiv);
            }
        }
    }
    
    updateMemoryIndicator() {
        const indicator = document.getElementById('memoryIndicator');
        const dot = indicator.querySelector('.indicator-dot');
        const text = indicator.querySelector('span:last-child');
        
        if (this.memoryEnabled) {
            dot.classList.add('active');
            text.textContent = 'Memory Active';
        } else {
            dot.classList.remove('active');
            text.textContent = 'Memory Disabled';
        }
    }
    
    updateSendButton() {
        const sendBtn = document.getElementById('sendBtn');
        sendBtn.disabled = this.isLoading;
    }
    
    scrollToBottom() {
        const container = document.getElementById('messagesContainer');
        container.scrollTop = container.scrollHeight;
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    capitalize(str) {
        return str.charAt(0).toUpperCase() + str.slice(1);
    }
    
    showError(message) {
        console.error(message);
        alert(message);
    }
    
    showToast(message) {
        alert(message);
    }
}

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.chatApp = new ChatApp();
});