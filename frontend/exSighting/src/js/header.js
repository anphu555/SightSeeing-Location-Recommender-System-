document.addEventListener("DOMContentLoaded", function() {
    // --- 1. HTML Khớp với CSS mới ---
    const headerHTML = `
    <header class="navbar-v3">
        <div class="logo" onclick="window.location.href='home.html'">
            <i class="fas fa-umbrella"></i>
            <span>exSighting</span>
        </div>
        
        <nav class="nav-links">
            
            <a href="about.html" class="nav-item">About us</a>
        </nav>
        
        <div id="authSection">
            <button class="user-actions-unsigned-in" id="unsignedBlock" onclick="handleLoginRedirect()">
                <div class="user-icon-bg"><i class="fas fa-user-circle"></i></div>
                <span class="sign-in-text">Sign In</span>
            </button>

            <div class="user-actions-signed-in" id="signedBlock" style="display: none;">
                <button class="user-profile-toggle">
                    <div class="user-icon-bg"><i class="fas fa-user-circle"></i></div>
                    <span class="username-text" id="displayUsername">User</span>
                    <i class="fas fa-caret-down" style="font-size: 0.8rem; margin-left: 5px;"></i>
                </button>
                
                <div class="user-dropdown-menu">
                    <a href="#"><i class="fas fa-user-circle"></i> Profile</a>
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

    // Hiển thị theo trạng thái đăng nhập
    if (token && username) {
        if(unsigned) unsigned.style.display = 'none';
        if(signed) signed.style.display = 'inline-block'; // CSS dùng inline-block
        if(displayUser) displayUser.textContent = username; 
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