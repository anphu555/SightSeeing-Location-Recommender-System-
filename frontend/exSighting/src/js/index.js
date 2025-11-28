// // File: exSighting/js/index.js

// document.addEventListener('DOMContentLoaded', () => {
//     // --- PHẦN 1: XỬ LÝ ĐĂNG NHẬP / ĐĂNG XUẤT ---
//     const token = localStorage.getItem('token');
//     const username = localStorage.getItem('username');
//     const statusDiv = document.getElementById('user-status');

//     if (token && username && statusDiv) {
//         // Render nội dung nếu đã đăng nhập
//         statusDiv.innerHTML = `
//             <span>Hello, ${username}</span>
//             <button id="btn-logout" style="margin-left: 10px; cursor: pointer;">Logout</button>
//         `;

//         // Gắn sự kiện click cho nút Logout vừa tạo (Thay vì dùng onclick trong HTML)
//         const logoutBtn = document.getElementById('btn-logout');
//         logoutBtn.addEventListener('click', () => {
//             localStorage.removeItem('token');
//             localStorage.removeItem('username');
//             window.location.reload();
//         });
//     }

//     // --- PHẦN 2: XỬ LÝ TÌM KIẾM ---
//     const inputEl = document.querySelector('.search-input');
//     const btnEl = document.querySelector('.search-button');

//     function goSearch() {
//         const text = (inputEl?.value || '').trim();
//         if (!text) {
//             alert('Hãy nhập gì đó');
//             return;
//         }
        
//         const params = new URLSearchParams({ text, k: '6' });
//         // Chuyển hướng sang trang result
//         window.location.href = `result.html?${params.toString()}`;
//     }

//     // Gắn sự kiện cho nút tìm kiếm và phím Enter
//     if (btnEl) btnEl.addEventListener('click', goSearch);
//     if (inputEl) inputEl.addEventListener('keydown', (e) => {
//         if (e.key === 'Enter') goSearch();
//     });
// });

const API_BASE = 'http://localhost:8000/api/v1';

document.addEventListener('DOMContentLoaded', () => {
    checkAuth();     // 1. Kiểm tra đăng nhập
    initBanner();    // 2. Khởi tạo Banner Slide
    loadPlaces();    // 3. Tải Popular Places
    initSearch();    // 4. Khởi tạo tìm kiếm
});

// --- 1. AUTH LOGIC ---
function checkAuth() {
    const token = localStorage.getItem('token');
    const user = localStorage.getItem('username');
    const unsigned = document.getElementById('unsignedBlock');
    const signed = document.getElementById('signedBlock');
    
    if (token && user) {
        document.getElementById('displayUsername').textContent = user;
        unsigned.style.display = 'none';
        signed.style.display = 'flex';
    } else {
        unsigned.style.display = 'flex';
        signed.style.display = 'none';
    }

    // Đăng xuất
    const logoutBtn = document.getElementById('btnLogout');
    if(logoutBtn) {
        logoutBtn.addEventListener('click', (e) => {
            e.preventDefault();
            localStorage.clear();
            window.location.reload();
        });
    }
}

// --- 2. BANNER SLIDER ---
function initBanner() {
    // Dữ liệu ảnh banner (Có thể thay link ảnh khác)
    const slidesData = [
        "https://images.unsplash.com/photo-1528127269322-539801943592?q=80&w=2070&auto=format&fit=crop",
        "https://images.unsplash.com/photo-1506748686214-e9df14d4d9d0?q=80&w=2070&auto=format&fit=crop",
        "https://images.unsplash.com/photo-1472214103451-9374bd1c798e?q=80&w=2070&auto=format&fit=crop"
    ];

    const slider = document.getElementById('bannerSlider');
    const dotsContainer = document.getElementById('bannerDots');
    
    // Render HTML
    slider.innerHTML = slidesData.map((url, i) => 
        `<div class="slide ${i===0?'active':''}" style="background-image: url('${url}')"></div>`
    ).join('');
    
    dotsContainer.innerHTML = slidesData.map((_, i) => 
        `<span class="dot ${i===0?'active':''}" data-index="${i}"></span>`
    ).join('');

    // Logic chạy slide
    const slides = document.querySelectorAll('.slide');
    const dots = document.querySelectorAll('.dot');
    let current = 0;
    let isAnimating = false;

    function goToSlide(index) {
        if(isAnimating || index === current) return;
        isAnimating = true;

        const prev = slides[current];
        const next = slides[index];
        current = index;

        prev.classList.remove('active');
        prev.classList.add('leave');
        
        next.classList.remove('leave');
        void next.offsetWidth; // Trigger reflow
        next.classList.add('active');

        dots.forEach(d => d.classList.remove('active'));
        dots[current].classList.add('active');

        setTimeout(() => {
            prev.classList.remove('leave');
            isAnimating = false;
        }, 1500); // Khớp với CSS transition 1.5s
    }

    // Auto play
    setInterval(() => goToSlide((current + 1) % slides.length), 7000);

    // Dot click
    dots.forEach(d => d.addEventListener('click', function() {
        goToSlide(parseInt(this.dataset.index));
    }));
}

// --- 3. POPULAR PLACES ---
async function loadPlaces() {
    // Dữ liệu mẫu Fallback (Nếu chưa nối backend)
    const fallbackData = [
        { id: 1, name: "HA LONG BAY", cost: "Medium", weather: "Cool", crowd: "Medium", img: "https://images.unsplash.com/photo-1528127269322-539801943592?q=80&w=2070" },
        { id: 2, name: "NHA TRANG", cost: "Low", weather: "Hot", crowd: "High", img: "https://images.unsplash.com/photo-1565691668615-5e60d5c08611?q=80&w=2070" },
        { id: 3, name: "SAPA", cost: "Low", weather: "Cold", crowd: "Medium", img: "https://images.unsplash.com/photo-1599229062397-6c8418047918?q=80&w=2070" },
        { id: 4, name: "DA LAT", cost: "Medium", weather: "Cool", crowd: "High", img: "https://images.unsplash.com/photo-1596328372690-e9b46571b402?q=80&w=2070" },
        { id: 5, name: "PHU QUOC", cost: "High", weather: "Warm", crowd: "Low", img: "https://images.unsplash.com/photo-1592350849318-7b9c9f2b879a?q=80&w=2070" },
        { id: 6, name: "HOI AN", cost: "Medium", weather: "Warm", crowd: "High", img: "https://images.unsplash.com/photo-1557750255-c76072a7aad1?q=80&w=2070" },
        { id: 7, name: "HUE", cost: "Low", weather: "Cool", crowd: "Medium", img: "https://images.unsplash.com/photo-1583486337220-333e882200be?q=80&w=2070" },
        { id: 8, name: "VUNG TAU", cost: "Low", weather: "Hot", crowd: "High", img: "https://images.unsplash.com/photo-1558611689-d64e83058814?q=80&w=2070" },
        { id: 9, name: "NINH BINH", cost: "Low", weather: "Cool", crowd: "Low", img: "https://images.unsplash.com/photo-1616639535315-998813a45c36?q=80&w=2070" }
    ];

    try {
        // Gọi API thật (Nếu server chạy thì bỏ comment dòng dưới)
        // const res = await fetch(`${API_BASE}/places`);
        // const data = await res.json();
        const data = fallbackData; // Dùng tạm fallback

        renderCarousel(data);
    } catch (err) {
        console.error("Lỗi tải Places:", err);
        renderCarousel(fallbackData);
    }
}

function renderCarousel(data) {
    const list = document.getElementById('placeCardList');
    const prev = document.getElementById('prevBtn');
    const next = document.getElementById('nextBtn');
    
    list.innerHTML = data.map(item => `
        <div class="place-card" onclick="window.location.href='results.html?q=${item.name}'">
            <img src="${item.img}" class="card-image">
            <div class="card-name-overlay"><h3>${item.name}</h3></div>
            <div class="card-content-wrapper">
                <div class="card-content">
                    <p><strong>Cost:</strong> ${item.cost}</p>
                    <p><strong>Weather:</strong> ${item.weather}</p>
                    <p><strong>Crowd:</strong> ${item.crowd}</p>
                    <button class="explore-btn">Explore Now!</button>
                </div>
            </div>
        </div>
    `).join('');

    // Logic Carousel (3 thẻ/lần, lặp vô tận)
    let step = 0;
    const CARD_WIDTH = 250;
    const GAP = 30;
    const PER_VIEW = 3;
    const DISTANCE = (CARD_WIDTH + GAP) * PER_VIEW;
    const MAX_STEPS = Math.ceil(data.length / PER_VIEW) - 1;

    function move(dir) {
        if (dir === 'next') step = (step < MAX_STEPS) ? step + 1 : 0;
        else step = (step > 0) ? step - 1 : MAX_STEPS;
        
        list.style.transform = `translateX(-${step * DISTANCE}px)`;
    }

    next.addEventListener('click', () => move('next'));
    prev.addEventListener('click', () => move('prev'));
}

// --- 4. SEARCH FUNCTION ---
function initSearch() {
    const input = document.getElementById('homeSearchInput');
    const btn = document.getElementById('homeSearchBtn');

    function goSearch() {
        const val = input.value.trim();
        if(val) window.location.href = `results.html?q=${encodeURIComponent(val)}`;
    }

    btn.addEventListener('click', goSearch);
    input.addEventListener('keypress', (e) => {
        if(e.key === 'Enter') goSearch();
    });
}