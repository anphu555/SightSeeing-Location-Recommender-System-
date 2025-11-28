const API_URL = 'http://localhost:8000/api/v1/auth/register'; 

async function handleRegister() {
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    const msg = document.getElementById('message');

    try {
        const response = await fetch(API_URL, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });

        if (response.status === 400) {
            msg.style.color = "red";
            msg.innerText = "Username already exists!";
            return;
        }

        if (!response.ok) throw new Error('Error');

        msg.style.color = "green";
        msg.innerText = "Đăng ký thành công! Đang chuyển hướng...";
        setTimeout(() => window.location.href = 'login.html', 1500);

    } catch (err) {
        msg.style.color = "red";
        msg.innerText = "Có lỗi xảy ra, vui lòng thử lại.";
    }
}