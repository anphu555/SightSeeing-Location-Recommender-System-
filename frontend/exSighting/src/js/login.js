const API_URL = 'http://localhost:8000/api/v1/auth/login'; 

// 1. Giữ nguyên logic xử lý
async function handleLogin(e) {
    if(e) e.preventDefault(); // Ngăn form reload trang

    const usernameInput = document.getElementById('username');
    const passwordInput = document.getElementById('password');
    const errorMsg = document.getElementById('error-msg');

    // Kiểm tra xem element có tồn tại không trước khi lấy value
    if (!usernameInput || !passwordInput) return;

    const username = usernameInput.value;
    const password = passwordInput.value;

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
        localStorage.setItem('token', data.access_token);
        localStorage.setItem('username', username);
        window.location.href = 'index.html';
    } catch (err) {
        if(errorMsg) {
            errorMsg.innerText = "Sai tên đăng nhập hoặc mật khẩu!";
            errorMsg.style.display = "block";
        }
    }
}

// 2. THÊM ĐOẠN NÀY ĐỂ BẮT SỰ KIỆN (Thay thế cho onclick bên HTML)
// Đảm bảo file HTML đã load xong mới tìm element
// document.addEventListener('DOMContentLoaded', () => {
//     // Tìm nút Login hoặc Form Login. 
//     // Giả sử nút login của bạn có id="btn-login" hoặc là nút submit trong form
//     const loginButton = document.querySelector('button[onclick="handleLogin()"]') || document.getElementById('btn-login') || document.querySelector('button[type="submit"]');

//     if (loginButton) {
//         loginButton.addEventListener('click', handleLogin);
//     }
// });

document.addEventListener('DOMContentLoaded', () => {
            // 1. Xử lý ấn Enter thì cũng gọi hàm đăng nhập
            const inputs = document.querySelectorAll('#loginForm input');
            inputs.forEach(input => {
                input.addEventListener('keypress', function (e) {
                    if (e.key === 'Enter') {
                        e.preventDefault(); // Chặn form submit
                        handleLogin();      // Gọi hàm trong file js/login.js
                    }
                });
            });

            // 2. Xử lý ẩn/hiện mật khẩu
            const toggleIcon = document.getElementById('togglePassword');
            const passwordInput = document.getElementById('password');
            
            if(toggleIcon && passwordInput) {
                toggleIcon.addEventListener('click', () => {
                    const type = passwordInput.getAttribute('type') === 'password' ? 'text' : 'password';
                    passwordInput.setAttribute('type', type);
                    toggleIcon.classList.toggle('fa-eye');
                    toggleIcon.classList.toggle('fa-eye-slash');
                });
            }
        });