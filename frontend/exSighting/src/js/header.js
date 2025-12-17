import { CONFIG } from './config.js';

document.addEventListener("DOMContentLoaded", function() {
    // Apply saved theme
    const savedTheme = localStorage.getItem('theme') || 'light';
    if (savedTheme === 'dark') {
        document.body.classList.add('dark-mode');
    }
    
    // --- 1. HTML Khớp với CSS mới ---
    const headerHTML = `
    <header class="navbar-v3">
        <div class="logo" onclick="window.location.href='home.html'">
            <i class="fas fa-umbrella"></i>
            <span>exSighting</span>
        </div>
        
        <nav class="nav-links">
            <a href="about.html" class="nav-item">About us</a>
            <a href="forum.html" class="nav-item">Forum</a>
        </nav>
        
        <div id="authSection">
            <button class="user-actions-unsigned-in" id="unsignedBlock" onclick="handleLoginRedirect()">
                <div class="user-icon-bg"><i class="fas fa-user-circle"></i></div>
                <span class="sign-in-text">Sign In</span>
            </button>

            <div class="user-actions-signed-in" id="signedBlock" style="display: none;">
                <button class="user-profile-toggle">
                    <div class="user-icon-bg" id="headerAvatarContainer"><i class="fas fa-user-circle"></i></div>
                    <span class="username-text" id="displayUsername">User</span>
                    <i class="fas fa-caret-down" style="font-size: 0.8rem; margin-left: 5px;"></i>
                </button>
                
                <div class="user-dropdown-menu">
                    <a href="profile.html"><i class="fas fa-user-circle"></i> Profile</a>
                    <a href="#"><i class="fas fa-cog"></i> Settings</a>
                    <div class="menu-divider"></div>
                    <a href="#" id="btnLogout"><i class="fas fa-sign-out-alt"></i> Log Out</a>
                </div>
            </div>
        </div>
    </header>
    `;

    // --- 2. Nhúng vào trang ---
    const placeholder = document.getElementById('header-placeholder');
    if (placeholder) {
        placeholder.innerHTML = headerHTML;
        runHeaderLogic();
    }
});

function handleLoginRedirect() {
    localStorage.setItem('returnUrl', window.location.href);
    window.location.href = 'login.html';
}

function runHeaderLogic() {
    const token = localStorage.getItem('token');
    const username = localStorage.getItem('username');
    
    const unsigned = document.getElementById('unsignedBlock');
    const signed = document.getElementById('signedBlock');
    const displayUser = document.getElementById('displayUsername');
    const headerAvatarContainer = document.getElementById('headerAvatarContainer');

    // Hiển thị theo trạng thái đăng nhập
    if (token && username) {
        if(unsigned) unsigned.style.display = 'none';
        if(signed) signed.style.display = 'inline-block'; // CSS dùng inline-block
        if(displayUser) displayUser.textContent = username;
        
        // Load và hiển thị avatar
        loadUserAvatar(token, headerAvatarContainer);
    } else {
        if(unsigned) unsigned.style.display = 'flex';
        if(signed) signed.style.display = 'none';
    }

    // Logic Logout
    const btnLogout = document.getElementById('btnLogout');
    if (btnLogout) {
        btnLogout.addEventListener('click', (e) => {
            e.preventDefault();
            localStorage.clear();
            window.location.reload();
        });
    }
    
    // Lưu ý: Dropdown menu giờ hoạt động bằng CSS Hover (.user-actions-signed-in:hover)
    // Nên không cần JS xử lý click để mở menu nữa.
}

// Function để load avatar từ backend
async function loadUserAvatar(token, avatarContainer) {
    if (!avatarContainer) return;
    
    try {
        // Check localStorage first
        const cachedAvatarUrl = localStorage.getItem('avatarUrl');
        if (cachedAvatarUrl) {
            updateAvatarDisplay(cachedAvatarUrl, avatarContainer);
        }
        
        // Fetch from backend để get latest avatar
        const response = await fetch(`${CONFIG.apiBase}/api/v1/auth/profile`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        
        if (response.ok) {
            const userData = await response.json();
            if (userData.avatar_url) {
                localStorage.setItem('avatarUrl', userData.avatar_url);
                updateAvatarDisplay(userData.avatar_url, avatarContainer);
            }
            if (userData.display_name) {
                localStorage.setItem('displayName', userData.display_name);
                const displayUser = document.getElementById('displayUsername');
                if (displayUser) {
                    displayUser.textContent = userData.display_name;
                }
            }
        }
    } catch (error) {
        console.error('Error loading user avatar:', error);
    }
}

function updateAvatarDisplay(avatarUrl, container) {
    if (!container || !avatarUrl) return;
    
    const fullAvatarUrl = avatarUrl.startsWith('http') 
        ? avatarUrl 
        : `${CONFIG.apiBase}${avatarUrl}`;
    
    container.innerHTML = `<img src="${fullAvatarUrl}" alt="Avatar" style="width: 100%; height: 100%; border-radius: 50%; object-fit: cover;">`;
}