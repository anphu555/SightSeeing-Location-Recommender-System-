const API_URL = 'http://localhost:8000/api/v1/auth/register'; 

async function handleRegister(e) {
    if(e) e.preventDefault();

    const usernameInput = document.getElementById('username');
    const passwordInput = document.getElementById('password');
    const msg = document.getElementById('message');

    if (!usernameInput || !passwordInput) return;

    const username = usernameInput.value;
    const password = passwordInput.value;

    try {
        const response = await fetch(API_URL, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });

        if (response.status === 400) {
            if(msg) {
                msg.style.color = "red";
                msg.innerText = "Username already exists!";
            }
            return;
        }

        if (!response.ok) throw new Error('Error');

        if(msg) {
            msg.style.color = "green";
            msg.innerText = "Registration successful! Redirecting...";
        }
        setTimeout(() => window.location.href = 'login.html', 100);

    } catch (err) {
        if(msg) {
            msg.style.color = "red";
            msg.innerText = "Something went wrong. Please try again.";
        }
    }
}

// THÊM ĐOẠN BẮT SỰ KIỆN
document.addEventListener('DOMContentLoaded', () => {
    // Tìm nút Register
    const registerButton = document.querySelector('button[onclick="handleRegister()"]') || document.getElementById('btn-register') || document.querySelector('button');

    if (registerButton) {
        registerButton.addEventListener('click', handleRegister);
    }
});