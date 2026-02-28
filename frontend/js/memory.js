import { memoryAPI } from './api.js';

// Memory Manager Class
export class MemoryManager {
    constructor() {
        this.memories = [];
        this.preferences = {};
        this.updateInterval = null;
    }
    
    async init() {
        await this.loadPreferences();
        this.startAutoUpdate();
    }
    
    async loadPreferences() {
        try {
            const data = await memoryAPI.getPreferences();
            this.preferences = data.preferences || {};
            this.renderPreferences();
        } catch (error) {
            console.error('Failed to load preferences:', error);
        }
    }
    
    renderPreferences() {
        const container = document.getElementById('preferencesList');
        if (!container) return;
        
        const preferences = this.preferences;
        
        if (Object.keys(preferences).length === 0) {
            container.innerHTML = '<p class="text-secondary">No preferences detected yet</p>';
            return;
        }
        
        container.innerHTML = '';
        for (const [key, values] of Object.entries(preferences)) {
            if (Array.isArray(values) && values.length > 0) {
                const categoryDiv = document.createElement('div');
                categoryDiv.className = 'preference-category';
                categoryDiv.innerHTML = `<h5>${this.formatKey(key)}</h5>`;
                values.forEach(value => {
                    categoryDiv.innerHTML += `<div class="preference-item">${this.escapeHtml(value)}</div>`;
                });
                container.appendChild(categoryDiv);
            }
        }
    }
    
    formatKey(key) {
        return key.charAt(0).toUpperCase() + key.slice(1);
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    startAutoUpdate() {
        // Update preferences every 30 seconds
        this.updateInterval = setInterval(() => {
            this.loadPreferences();
        }, 30000);
    }
    
    stopAutoUpdate() {
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
        }
    }
}

// Initialize memory manager
export const memoryManager = new MemoryManager();