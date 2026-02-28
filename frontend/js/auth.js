// API Configuration
const API_BASE_URL = 'http://localhost:8000/api';

// Register function
async function register(username, email, password) {
    const response = await fetch(`${API_BASE_URL}/register`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ username, email, password })
    });
    return await response.json();
}

// Login function
async function login(username, password) {
    const formData = new URLSearchParams();
    formData.append('username', username);
    formData.append('password', password);
    
    const response = await fetch(`${API_BASE_URL}/login`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: formData
    });
    return await response.json();
}

// Check if user is authenticated
export function isAuthenticated() {
    return !!localStorage.getItem('token');
}

// Require authentication
export function requireAuth() {
    if (!isAuthenticated() && !window.location.pathname.includes('login') && !window.location.pathname.includes('register')) {
        window.location.href = '/login.html';
    }
}

// Handle login form
export function initLogin() {
    const form = document.getElementById('loginForm');
    if (!form) return;
    
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const username = document.getElementById('username').value;
        const password = document.getElementById('password').value;
        const loginBtn = document.getElementById('loginBtn');
        const errorMessage = document.getElementById('errorMessage');
        
        loginBtn.disabled = true;
        loginBtn.querySelector('span').classList.add('hidden');
        loginBtn.querySelector('.loading-spinner').classList.remove('hidden');
        errorMessage.classList.add('hidden');
        
        try {
            const data = await login(username, password);
            
            if (data.access_token) {
                localStorage.setItem('token', data.access_token);
                localStorage.setItem('username', username);
                window.location.href = '/';
            } else {
                throw new Error(data.detail || 'Login failed');
            }
        } catch (error) {
            errorMessage.textContent = error.message;
            errorMessage.classList.remove('hidden');
        } finally {
            loginBtn.disabled = false;
            loginBtn.querySelector('span').classList.remove('hidden');
            loginBtn.querySelector('.loading-spinner').classList.add('hidden');
        }
    });
}

// Handle register form
export function initRegister() {
    const form = document.getElementById('registerForm');
    if (!form) return;
    
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const username = document.getElementById('username').value;
        const email = document.getElementById('email').value;
        const password = document.getElementById('password').value;
        const confirmPassword = document.getElementById('confirmPassword').value;
        const registerBtn = document.getElementById('registerBtn');
        const errorMessage = document.getElementById('errorMessage');
        const successMessage = document.getElementById('successMessage');
        
        if (password !== confirmPassword) {
            errorMessage.textContent = 'Passwords do not match';
            errorMessage.classList.remove('hidden');
            return;
        }
        
        registerBtn.disabled = true;
        registerBtn.querySelector('span').classList.add('hidden');
        registerBtn.querySelector('.loading-spinner').classList.remove('hidden');
        errorMessage.classList.add('hidden');
        successMessage.classList.add('hidden');
        
        try {
            const data = await register(username, email, password);
            
            if (data.id) {
                successMessage.textContent = 'Registration successful! Redirecting to login...';
                successMessage.classList.remove('hidden');
                setTimeout(() => {
                    window.location.href = '/login.html';
                }, 2000);
            } else {
                throw new Error(data.detail || 'Registration failed');
            }
        } catch (error) {
            errorMessage.textContent = error.message;
            errorMessage.classList.remove('hidden');
        } finally {
            registerBtn.disabled = false;
            registerBtn.querySelector('span').classList.remove('hidden');
            registerBtn.querySelector('.loading-spinner').classList.add('hidden');
        }
    });
}

// Handle logout
export function initLogout() {
    const logoutBtn = document.getElementById('logoutBtn');
    if (!logoutBtn) return;
    
    logoutBtn.addEventListener('click', () => {
        localStorage.removeItem('token');
        localStorage.removeItem('username');
        window.location.href = '/login.html';
    });
}

// Initialize based on page
document.addEventListener('DOMContentLoaded', () => {
    if (window.location.pathname.includes('login')) {
        initLogin();
    } else if (window.location.pathname.includes('register')) {
        initRegister();
    } else {
        requireAuth();
        initLogout();
    }
});