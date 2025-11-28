// File: exSighting/js/index.js

document.addEventListener('DOMContentLoaded', () => {
    // --- PHẦN 1: XỬ LÝ ĐĂNG NHẬP / ĐĂNG XUẤT ---
    const token = localStorage.getItem('token');
    const username = localStorage.getItem('username');
    const statusDiv = document.getElementById('user-status');

    if (token && username && statusDiv) {
        // Render nội dung nếu đã đăng nhập
        statusDiv.innerHTML = `
            <span>Hello, ${username}</span>
            <button id="btn-logout" style="margin-left: 10px; cursor: pointer;">Logout</button>
        `;

        // Gắn sự kiện click cho nút Logout vừa tạo (Thay vì dùng onclick trong HTML)
        const logoutBtn = document.getElementById('btn-logout');
        logoutBtn.addEventListener('click', () => {
            localStorage.removeItem('token');
            localStorage.removeItem('username');
            window.location.reload();
        });
    }

    // --- PHẦN 2: XỬ LÝ TÌM KIẾM ---
    const inputEl = document.querySelector('.search-input');
    const btnEl = document.querySelector('.search-button');

    function goSearch() {
        const text = (inputEl?.value || '').trim();
        if (!text) {
            alert('Hãy nhập gì đó');
            return;
        }
        
        const params = new URLSearchParams({ text, k: '6' });
        // Chuyển hướng sang trang result
        window.location.href = `result.html?${params.toString()}`;
    }

    // Gắn sự kiện cho nút tìm kiếm và phím Enter
    if (btnEl) btnEl.addEventListener('click', goSearch);
    if (inputEl) inputEl.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') goSearch();
    });
});