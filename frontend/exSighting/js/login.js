// Nếu dùng localhost thì URL này, nếu deploy thì đổi lại
const API_URL = 'http://localhost:8000/api/v1/auth/login'; 

async function handleLogin() {
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    const errorMsg = document.getElementById('error-msg');

    // OAuth2 yêu cầu gửi data dạng Form Data
    const formData = new URLSearchParams();
    formData.append('username', username);
    formData.append('password', password);

    try {
        const response = await fetch(API_URL, {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: formData
        });

        if (!response.ok) throw new Error('Login failed');

        const data = await response.json();
        
        // Lưu token vào localStorage
        localStorage.setItem('token', data.access_token);
        localStorage.setItem('username', username);
        
        // Chuyển hướng về trang chủ
        window.location.href = 'index.html';
    } catch (err) {
        errorMsg.innerText = "Sai tên đăng nhập hoặc mật khẩu!";
        errorMsg.style.display = "block";
    }
}