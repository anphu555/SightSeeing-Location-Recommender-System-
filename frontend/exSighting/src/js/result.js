document.addEventListener('DOMContentLoaded', () => {
    checkAuth();
    
    // --- 1. DỮ LIỆU GIẢ LẬP (MOCK DATA) ---
    // Dùng để test giao diện khi chưa có Backend
    const mockResults = [
        { id: 101, name: "Ha Long Bay", province: "Quang Ninh", score: 4.8, themes: ['beach', 'island'] },
        { id: 105, name: "Nha Trang", province: "Khanh Hoa", score: 4.5, themes: ['beach'] },
        { id: 106, name: "Sapa", province: "Lao Cai", score: 4.7, themes: ['mountain'] },
        { id: 201, name: "Bai Da Song Hong", province: "Hanoi", score: 4.2, themes: ['city'] },
        { id: 108, name: "Phu Quoc", province: "Kien Giang", score: 4.9, themes: ['island', 'beach'] },
        { id: 104, name: "Da Lat", province: "Lam Dong", score: 4.6, themes: ['mountain', 'flower'] }
    ];

    // --- 2. RENDER GIAO DIỆN ---
    const grid = document.getElementById('resultsGrid');
    const count = document.getElementById('totalCount');

    if (grid) {
        // Cập nhật số lượng kết quả
        if(count) count.innerText = mockResults.length;
        
        // Tạo HTML cho từng thẻ
        grid.innerHTML = mockResults.map(item => {
            // Chọn ảnh ngẫu nhiên theo chủ đề (Theme)
            let imgSrc = "https://images.unsplash.com/photo-1528127269322-539801943592?q=80&w=2070"; // Mặc định: Biển
            
            if(item.themes.includes('mountain')) {
                imgSrc = "https://images.unsplash.com/photo-1599229062397-6c8418047918?q=80&w=2070"; // Núi
            } else if(item.themes.includes('city')) {
                imgSrc = "https://images.unsplash.com/photo-1557750255-c76072a7aad1?q=80&w=2070"; // Thành phố
            }

            return `
            <div class="result-card" onclick="goToDetail('${item.id}')" style="cursor: pointer;">
                <div class="card-img-top">
                    <img src="${imgSrc}" alt="${item.name}">
                    <div class="view-badge"><i class="fas fa-star"></i> ${item.score}</div>
                </div>
                <div class="card-body">
                    <h4 class="card-title">${item.name}</h4>
                    <p class="card-subtitle">${item.province}</p>
                </div>
                <div class="card-footer">
                    <button class="icon-action like-btn" onclick="event.stopPropagation()"><i class="fas fa-thumbs-up"></i></button>
                    <button class="icon-action dislike-btn" onclick="event.stopPropagation()"><i class="fas fa-thumbs-down"></i></button>
                </div>
            </div>
            `;
        }).join('');
    }

    // --- 3. XỬ LÝ DROPDOWN SORT (Giao diện) ---
    initSortDropdown();
});

// --- HÀM CHUYỂN TRANG ---
window.goToDetail = function(id) {
    window.location.href = `detail.html?id=${id}`;
};

// --- LOGIC AUTH (Đăng nhập/Đăng xuất) ---
function checkAuth() {
    const token = localStorage.getItem('token');
    const user = localStorage.getItem('username');
    const unsigned = document.getElementById('unsignedBlock');
    const signed = document.getElementById('signedBlock');
    
    if (token && user) {
        if(document.getElementById('displayUsername')) {
            document.getElementById('displayUsername').textContent = user;
        }
        if(unsigned) unsigned.style.display = 'none';
        if(signed) signed.style.display = 'flex';
    } else {
        if(unsigned) unsigned.style.display = 'flex';
        if(signed) signed.style.display = 'none';
    }

    const logoutBtn = document.getElementById('btnLogout');
    if(logoutBtn) {
        logoutBtn.addEventListener('click', (e) => {
            e.preventDefault();
            localStorage.clear();
            window.location.reload();
        });
    }
}

// --- LOGIC DROPDOWN SORT ---
function initSortDropdown() {
    const dropdown = document.getElementById('customSort');
    if (!dropdown) return;

    const trigger = dropdown.querySelector('.sort-trigger');
    const options = dropdown.querySelectorAll('.sort-option');
    const display = document.getElementById('currentSortValue');

    if (trigger) {
        trigger.addEventListener('click', (e) => {
            e.stopPropagation();
            dropdown.classList.toggle('open');
        });
    }

    options.forEach(opt => {
        opt.addEventListener('click', () => {
            if(display) display.innerText = opt.innerText;
            options.forEach(o => o.classList.remove('active'));
            opt.classList.add('active');
            dropdown.classList.remove('open');
            console.log("Sort by:", opt.dataset.value); // Để dev xem log
        });
    });

    document.addEventListener('click', (e) => {
        if(!dropdown.contains(e.target)) dropdown.classList.remove('open');
    });
}