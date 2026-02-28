import { authAPI } from './api.js';

// Check if user is authenticated
export function isAuthenticated() {
    return !!localStorage.getItem('token');
}

// Redirect to login if not authenticated
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
        
        // Show loading
        loginBtn.disabled = true;
        loginBtn.querySelector('span').classList.add('hidden');
        loginBtn.querySelector('.loading-spinner').classList.remove('hidden');
        errorMessage.classList.add('hidden');
        
        try {
            const data = await authAPI.login(username, password);
            
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

// Handle registration form
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
        
        // Validate passwords match
        if (password !== confirmPassword) {
            errorMessage.textContent = 'Passwords do not match';
            errorMessage.classList.remove('hidden');
            return;
        }
        
        // Show loading
        registerBtn.disabled = true;
        registerBtn.querySelector('span').classList.add('hidden');
        registerBtn.querySelector('.loading-spinner').classList.remove('hidden');
        errorMessage.classList.add('hidden');
        successMessage.classList.add('hidden');
        
        try {
            await authAPI.register({ username, email, password });
            
            successMessage.textContent = 'Registration successful! Redirecting to login...';
            successMessage.classList.remove('hidden');
            
            // Redirect to login after 2 seconds
            setTimeout(() => {
                window.location.href = '/login.html';
            }, 2000);
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

// Initialize auth based on page
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