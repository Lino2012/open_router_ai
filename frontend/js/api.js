// API Configuration
const API_BASE_URL = window.location.hostname === 'localhost' 
    ? 'http://localhost:8000/api'
    : '/api';

// Helper function for API calls
async function apiCall(endpoint, options = {}) {
    const token = localStorage.getItem('token');
    
    const defaultHeaders = {
        'Content-Type': 'application/json',
        ...(token && { 'Authorization': `Bearer ${token}` })
    };
    
    try {
        const response = await fetch(`${API_BASE_URL}${endpoint}`, {
            ...options,
            headers: {
                ...defaultHeaders,
                ...options.headers
            }
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.detail || 'API call failed');
        }
        
        return data;
    } catch (error) {
        console.error('API Error:', error);
        throw error;
    }
}

// Authentication APIs
export const authAPI = {
    register: (userData) => apiCall('/register', {
        method: 'POST',
        body: JSON.stringify(userData)
    }),
    
    login: (username, password) => {
        const formData = new URLSearchParams();
        formData.append('username', username);
        formData.append('password', password);
        
        return fetch(`${API_BASE_URL}/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: formData
        }).then(res => res.json());
    }
};

// Chat APIs
export const chatAPI = {
    sendMessage: (message, sessionId = null, memoryEnabled = true, metadata = {}) => {
        const payload = {
            message,
            session_id: sessionId,
            memory_enabled: memoryEnabled,
            metadata: metadata
        };
        
        if (!sessionId) delete payload.session_id;
        
        return apiCall('/chat', {
            method: 'POST',
            body: JSON.stringify(payload)
        });
    },
    
    getSessions: () => apiCall('/sessions'),
    
    deleteSession: (sessionId) => apiCall(`/session/${sessionId}`, {
        method: 'DELETE'
    }),
    
    getSessionMessages: (sessionId) => apiCall(`/session/${sessionId}/messages`)
};

// Memory APIs
export const memoryAPI = {
    getPreferences: () => apiCall('/memory/preferences'),
    
    getRecentMemories: (limit = 10, type = null) => {
        let url = `/memory/recent?limit=${limit}`;
        if (type) url += `&memory_type=${type}`;
        return apiCall(url);
    },
    
    storeMemory: (content, type = 'general', metadata = {}) => apiCall('/memory/store', {
        method: 'POST',
        body: JSON.stringify({ content, type, metadata })
    }),
    
    searchMemories: (query, limit = 5, memoryType = null) => apiCall('/memory/search', {
        method: 'POST',
        body: JSON.stringify({ query, limit, memory_type: memoryType })
    })
};