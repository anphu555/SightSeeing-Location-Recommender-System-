import { CONFIG } from './config.js';

// Toast notification variables
let toastTimeout;
let keyListener;

// Toast notification function
function showToast(message, type = 'success') {
    const toast = document.getElementById('toast');
    const toastMessage = document.getElementById('toastMessage');
    const icon = toast.querySelector('i');
    
    // Clear previous timeout and listener
    if (toastTimeout) clearTimeout(toastTimeout);
    if (keyListener) document.removeEventListener('keydown', keyListener);
    
    // Set message and icon
    toastMessage.textContent = message;
    
    if (type === 'success') {
        icon.className = 'fas fa-check-circle';
        toast.style.background = 'linear-gradient(135deg, #14838B 0%, #0d5f66 100%)';
    } else if (type === 'error') {
        icon.className = 'fas fa-exclamation-circle';
        toast.style.background = 'linear-gradient(135deg, #e74c3c 0%, #c0392b 100%)';
    } else if (type === 'warning') {
        icon.className = 'fas fa-info-circle';
        toast.style.background = 'linear-gradient(135deg, #f39c12 0%, #e67e22 100%)';
    }
    
    // Show toast
    toast.classList.remove('hide');
    toast.classList.add('show');
    
    // Hide after 3s
    toastTimeout = setTimeout(() => {
        hideToast();
    }, 3000);
    
    // Close on any key press
    keyListener = (e) => {
        hideToast();
    };
    document.addEventListener('keydown', keyListener, { once: true });
}

function hideToast() {
    const toast = document.getElementById('toast');
    toast.classList.add('hide');
    
    setTimeout(() => {
        toast.classList.remove('show', 'hide');
    }, 400);
    
    if (toastTimeout) clearTimeout(toastTimeout);
    if (keyListener) document.removeEventListener('keydown', keyListener);
}

document.addEventListener('DOMContentLoaded', () => {
    checkAuth();
    initTheme();
    initThemeButtons();
});

function checkAuth() {
    const token = localStorage.getItem('token');
    const username = localStorage.getItem('username');
    
    const unsigned = document.getElementById('unsignedBlock');
    const signed = document.getElementById('signedBlock');
    const displayUser = document.getElementById('displayUsername');
    const headerAvatarContainer = document.getElementById('headerAvatarContainer');

    if (token && username) {
        if(unsigned) unsigned.style.display = 'none';
        if(signed) signed.style.display = 'inline-block';
        
        // Hiển thị display name thay vì username
        const displayName = localStorage.getItem('displayName') || username;
        if(displayUser) displayUser.textContent = displayName;
        
        // Load avatar
        if (headerAvatarContainer) {
            const avatarUrl = localStorage.getItem('avatarUrl');
            if (avatarUrl) {
                const fullAvatarUrl = avatarUrl.startsWith('http') ? avatarUrl : `${CONFIG.apiBase}${avatarUrl}`;
                headerAvatarContainer.innerHTML = `<img src="${fullAvatarUrl}" alt="Avatar" style="width: 100%; height: 100%; border-radius: 50%; object-fit: cover;">`;
            }
        }
    } else {
        // Nếu chưa login, chuyển về trang login
        window.location.href = 'login.html';
        return;
    }

    // Logout
    const btnLogout = document.getElementById('btnLogout');
    if (btnLogout) {
        btnLogout.addEventListener('click', (e) => {
            e.preventDefault();
            localStorage.clear();
            window.location.href = 'login.html';
        });
    }
}

// Initialize theme from localStorage
function initTheme() {
    const savedTheme = localStorage.getItem('theme') || 'light';
    applyTheme(savedTheme);
}

// Apply theme to body
function applyTheme(theme) {
    if (theme === 'dark') {
        document.body.classList.add('dark-mode');
    } else {
        document.body.classList.remove('dark-mode');
    }
    
    // Update active button
    document.querySelectorAll('.theme-btn').forEach(btn => {
        if (btn.dataset.theme === theme) {
            btn.classList.add('active');
        } else {
            btn.classList.remove('active');
        }
    });
    
    // Save to localStorage
    localStorage.setItem('theme', theme);
}

// Initialize theme toggle buttons
function initThemeButtons() {
    const themeButtons = document.querySelectorAll('.theme-btn');
    
    themeButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            const theme = btn.dataset.theme;
            applyTheme(theme);
            
            // Show toast notification
            const themeName = theme === 'dark' ? 'Dark Mode' : 'Light Mode';
            showToast(`✓ ${themeName} activated!`);
        });
    });
}
