document.addEventListener('DOMContentLoaded', () => {
    checkAuth();
    
    // Khởi tạo chức năng tìm kiếm ngay khi trang load
    handleResultPageSearch(); 
    
    // --- 1. DỮ LIỆU GIẢ LẬP ĐẦY ĐỦ (10 ĐỊA ĐIỂM) ---
    // Khớp ID với file detail.html để khi bấm vào không bị lỗi
    const mockResults = [
        { id: "101", name: "Ha Long Bay", province: "Quang Ninh", score: 4.8, themes: ['beach', 'island'] },
        { id: "102", name: "Tuan Chau Park", province: "Quang Ninh", score: 4.2, themes: ['beach'] },
        { id: "103", name: "Hoi An", province: "Quang Nam", score: 4.9, themes: ['city'] },
        { id: "104", name: "Da Lat", province: "Lam Dong", score: 4.6, themes: ['mountain', 'flower'] },
        { id: "105", name: "Nha Trang", province: "Khanh Hoa", score: 4.5, themes: ['beach'] },
        { id: "106", name: "Sapa", province: "Lao Cai", score: 4.7, themes: ['mountain'] },
        { id: "107", name: "Hue", province: "Thua Thien Hue", score: 4.6, themes: ['city'] },
        { id: "108", name: "Phu Quoc", province: "Kien Giang", score: 4.9, themes: ['island', 'beach'] },
        { id: "109", name: "Vung Tau", province: "Ba Ria - Vung Tau", score: 4.3, themes: ['beach'] },
        { id: "110", name: "Ninh Binh", province: "Ninh Binh", score: 4.7, themes: ['mountain'] }
    ];

    // --- 2. XỬ LÝ LỌC KẾT QUẢ ---
    const grid = document.getElementById('resultsGrid');
    const count = document.getElementById('totalCount');

    // Lấy từ khóa từ URL (ví dụ: results.html?q=Hoi An)
    const params = new URLSearchParams(window.location.search);
    const query = params.get('q') || "";
    
    // Logic lọc: Tìm theo tên HOẶC theo tỉnh thành (không phân biệt hoa thường)
    const filteredResults = query 
        ? mockResults.filter(p => 
            p.name.toLowerCase().includes(query.toLowerCase()) || 
            p.province.toLowerCase().includes(query.toLowerCase())
          )
        : mockResults;

    // --- 3. RENDER GIAO DIỆN ---
    if (grid) {
        // Cập nhật số lượng
        if(count) count.innerText = filteredResults.length;
        
        if (filteredResults.length === 0) {
            grid.innerHTML = `<p style="grid-column: 1/-1; text-align: center; font-size: 1.2rem; color: #666; margin-top: 50px;">
                No results found for "<b>${query}</b>". 
            </p>`;
        } else {
            // Tạo HTML danh sách
            grid.innerHTML = filteredResults.map(item => {
                // Chọn ảnh ngẫu nhiên theo chủ đề
                let imgSrc = "https://images.unsplash.com/photo-1528127269322-539801943592?q=80&w=2070"; // Mặc định: Biển
                
                if(item.themes.includes('mountain')) {
                    imgSrc = "https://images.unsplash.com/photo-1599229062397-6c8418047918?q=80&w=2070";
                } else if(item.themes.includes('city')) {
                    imgSrc = "https://images.unsplash.com/photo-1557750255-c76072a7aad1?q=80&w=2070";
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
    }

    initSortDropdown();
});

// === HÀM XỬ LÝ TÌM KIẾM (SEARCH LOGIC) ===
function handleResultPageSearch() {
    const input = document.getElementById('resultsPageInput');
    const btn = document.getElementById('resultsPageSearchBtn');

    // 1. Điền lại từ khóa cũ vào ô input để người dùng biết mình đang tìm gì
    const params = new URLSearchParams(window.location.search);
    const currentQuery = params.get('q');
    if (input && currentQuery) {
        input.value = currentQuery;
    }

    // 2. Hàm thực thi tìm kiếm
    const doSearch = () => {
        if (!input) return;
        const val = input.value.trim();
        if (val) {
            // Reload trang với tham số ?q=...
            window.location.href = `results.html?q=${encodeURIComponent(val)}`;
        } else {
            // Nếu rỗng thì về trang result gốc (hiện tất cả)
            window.location.href = `results.html`;
        }
    };

    // 3. Gắn sự kiện Click và Enter
    if (btn) {
        btn.onclick = doSearch; // Gán trực tiếp để tránh duplicate event
    }
    if (input) {
        input.onkeypress = (e) => {
            if (e.key === 'Enter') doSearch();
        };
    }
}

// --- CÁC HÀM HỖ TRỢ KHÁC ---
window.goToDetail = function(id) {
    window.location.href = `detail.html?id=${id}`;
};

function checkAuth() {
    const token = localStorage.getItem('token');
    const user = localStorage.getItem('username');
    const unsigned = document.getElementById('unsignedBlock');
    const signed = document.getElementById('signedBlock');
    
    if (token && user) {
        const nameDisplay = document.getElementById('displayUsername');
        if(nameDisplay) nameDisplay.textContent = user;
        if(unsigned) unsigned.style.display = 'none';
        if(signed) signed.style.display = 'flex';
    } else {
        if(unsigned) unsigned.style.display = 'flex';
        if(signed) signed.style.display = 'none';
    }

    const logoutBtn = document.getElementById('btnLogout');
    if(logoutBtn) {
        logoutBtn.onclick = (e) => {
            e.preventDefault();
            localStorage.clear();
            window.location.reload();
        };
    }
}

function initSortDropdown() {
    const dropdown = document.getElementById('customSort');
    if (!dropdown) return;
    const trigger = dropdown.querySelector('.sort-trigger');
    const options = dropdown.querySelectorAll('.sort-option');
    const display = document.getElementById('currentSortValue');

    trigger.onclick = (e) => {
        e.stopPropagation();
        dropdown.classList.toggle('open');
    };

    options.forEach(opt => {
        opt.onclick = () => {
            if(display) display.innerText = opt.innerText;
            options.forEach(o => o.classList.remove('active'));
            opt.classList.add('active');
            dropdown.classList.remove('open');
        };
    });

    document.onclick = (e) => {
        if(!dropdown.contains(e.target)) dropdown.classList.remove('open');
    };
}