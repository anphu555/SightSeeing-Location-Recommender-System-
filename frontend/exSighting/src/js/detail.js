// === 1. DỮ LIỆU ĐỊA ĐIỂM (Đã cập nhật nội dung Highlights đầy đủ) ===
    const placesData = {
        "101": {
            name: "HA LONG BAY",
            location: "Quang Ninh", distance: "123",
            // Nội dung Description chứa HTML chuẩn cho Highlights
            desc: `
                Ha Long Bay features thousands of limestone karsts and isles in various shapes and sizes.
                <br><br>
                <b>Highlights:</b>
                <ul style="margin-top:5px; padding-left:20px; list-style-type: disc;">
                    <li>Boat cruises</li>
                    <li>Cave exploration (Sung Sot, Thien Cung)</li>
                    <li>Kayaking & Swimming</li>
                    <li>Visiting pearl farms</li>
                </ul>
            `,
            // Danh sách ảnh (Đã nhân bản để test chuyển trang)
            images: [
                    // Trang 1
                "https://images.unsplash.com/photo-1528127269322-539801943592?q=80&w=2070",
                "https://images.unsplash.com/photo-1504457047772-27faf1c00561?q=80&w=2070",
                "https://images.unsplash.com/photo-1464983308960-49ad68803cc2?q=80&w=2070",
                "https://images.unsplash.com/photo-1559592413-7cec4d0cae2b?q=80&w=2070",
                // Trang 2
                "https://images.unsplash.com/photo-1506748686214-e9df14d4d9d0?q=80&w=2070",
                "https://images.unsplash.com/photo-1472214103451-9374bd1c798e?q=80&w=2070",
                "https://images.unsplash.com/photo-1533285860268-c9c004c27a20?q=80&w=2070",
                "https://images.unsplash.com/photo-1616383637651-72251a700320?q=80&w=2070",
                // Trang 3
                "https://images.unsplash.com/photo-1596328372690-e9b46571b402?q=80&w=2070",
                "https://images.unsplash.com/photo-1583486337220-333e882200be?q=80&w=2070"
            ],
            reviews: [{ user: "Sarah Nguyen", avatar: "https://randomuser.me/api/portraits/women/44.jpg", comment: "The scenery is absolutely breathtaking!", photos: [] }]
        },
        // (Các ID khác tự động fallback nếu thiếu dữ liệu, code vẫn chạy ổn)
        "102": { name: "TUAN CHAU PARK", location: "Quang Ninh", distance: "130", desc: "An entertainment complex.", images: ["https://images.unsplash.com/photo-1565691668615-5e60d5c08611?q=80&w=2070"], reviews: [] },
        "103": { name: "HOI AN", location: "Quang Nam", distance: "800", desc: "Ancient Town.", images: ["https://images.unsplash.com/photo-1557750255-c76072a7aad1?q=80&w=2070"], reviews: [] },
        "104": { name: "DA LAT", location: "Lam Dong", distance: "300", desc: "City of Flowers.", images: ["https://images.unsplash.com/photo-1596328372690-e9b46571b402?q=80&w=2070"], reviews: [] },
        "105": { name: "NHA TRANG", location: "Khanh Hoa", distance: "450", desc: "Beach City.", images: ["https://images.unsplash.com/photo-1570535926348-18302f741544?q=80&w=2070"], reviews: [] },
        "106": { name: "SAPA", location: "Lao Cai", distance: "320", desc: "Mountain Town.", images: ["https://images.unsplash.com/photo-1565257913380-010534c0e660?q=80&w=2070"], reviews: [] },
        "107": { name: "HUE", location: "Thua Thien Hue", distance: "660", desc: "Imperial City.", images: ["https://images.unsplash.com/photo-1583486337220-333e882200be?q=80&w=2070"], reviews: [] },
        "108": { name: "PHU QUOC", location: "Kien Giang", distance: "1200", desc: "Island Paradise.", images: ["https://images.unsplash.com/photo-1592350849318-7b9c9f2b879a?q=80&w=2070"], reviews: [] },
        "109": { name: "VUNG TAU", location: "Ba Ria - Vung Tau", distance: "100", desc: "Seaside Town.", images: ["https://images.unsplash.com/photo-1558611689-d64e83058814?q=80&w=2070"], reviews: [] },
        "110": { name: "NINH BINH", location: "Ninh Binh", distance: "90", desc: "Ha Long on Land.", images: ["https://images.unsplash.com/photo-1616639535315-998813a45c36?q=80&w=2070"], reviews: [] }
    };

    // === 2. QUẢN LÝ TRẠNG THÁI ===
let currentImgIndex = 0;
let currentImagesList = [];
const ITEMS_PER_PAGE = 4; // Số lượng ảnh hiển thị 1 lần

// === 3. HÀM ĐIỀU HƯỚNG (Next/Prev) ===
window.slideThumbs = function(direction) {
    let newIndex = currentImgIndex + direction;

    // Loop: Hết ảnh quay về đầu
    if (newIndex < 0) newIndex = currentImagesList.length - 1;
    if (newIndex >= currentImagesList.length) newIndex = 0;

    updateGallery(newIndex);
};

window.clickThumb = function(index) {
    updateGallery(index);
};

// === 4. CORE LOGIC: CẬP NHẬT GIAO DIỆN & TRƯỢT TỐP ẢNH ===
function updateGallery(index) {
    currentImgIndex = index;

    // 1. Đổi ảnh lớn
    const mainImg = document.getElementById('detailMainImg');
    if(mainImg) mainImg.src = currentImagesList[index];

    // 2. Highlight ảnh nhỏ
    const allThumbs = document.querySelectorAll('.thumb-box');
    allThumbs.forEach((box, i) => {
        if (i === index) box.classList.add('active');
        else box.classList.remove('active');
    });

    // 3. TỰ ĐỘNG TRƯỢT THEO TRANG (Logic Mới)
    const track = document.getElementById('detailThumbs');
    const viewport = document.querySelector('.thumb-viewport');
    
    if (track && viewport) {
        // Tính xem ảnh hiện tại đang ở "Trang" nào (0, 1, 2...)
        const pageIndex = Math.floor(index / ITEMS_PER_PAGE);
        
        // Lấy chiều rộng khung nhìn thực tế (để trượt đúng 1 khung)
        const viewportWidth = viewport.clientWidth; 
        
        // Tính toán khoảng cách trượt
        const scrollAmount = -(pageIndex * viewportWidth);
        
        track.style.transform = `translateX(${scrollAmount}px)`;
    }
}

// === 5. KHỞI TẠO ===
document.addEventListener('DOMContentLoaded', () => {
    checkAuth();
    initHeaderDropdown();

    const params = new URLSearchParams(window.location.search);
    const id = params.get('id') || "101"; 
    const data = placesData[id] || placesData["101"];
    currentImagesList = data.images;

    renderPage(data);
    renderRecs(id);

    // Bàn phím
    document.addEventListener('keydown', (e) => {
        if (e.key === 'ArrowRight') { e.preventDefault(); window.slideThumbs(1); }
        else if (e.key === 'ArrowLeft') { e.preventDefault(); window.slideThumbs(-1); }
    });
});

function renderPage(data) {
    document.getElementById('detailTitle').innerText = data.name;
    document.getElementById('detailLocation').innerText = data.location;
    document.getElementById('detailDistance').innerText = data.distance + " km from you";
    document.getElementById('detailDesc').innerHTML = data.desc;
    
    const thumbsContainer = document.getElementById('detailThumbs');
    if (thumbsContainer) {
        thumbsContainer.innerHTML = data.images.map((img, i) => `
            <div class="thumb-box" onclick="clickThumb(${i})">
                <img src="${img}">
            </div>
        `).join('');
    }
    
    // Khởi tạo gallery ở ảnh đầu tiên
    updateGallery(0);

    const reviewsContainer = document.getElementById('reviewsList');
    if(data.reviews.length > 0) {
        reviewsContainer.innerHTML = data.reviews.map(rev => `
            <div class="review-card">
                <img src="${rev.avatar}" class="reviewer-avatar">
                <div class="review-content">
                    <h4>${rev.user}</h4><p>${rev.comment}</p>
                </div>
            </div>`).join('');
    }
}

// (Giữ nguyên các hàm renderRecs, checkAuth, initHeaderDropdown như cũ)
function renderRecs(currentId) {
    const list = document.getElementById('recommendationList');
    if(list) {
        const otherIds = Object.keys(placesData).filter(k => k !== currentId).slice(0, 3);
        list.innerHTML = otherIds.map(k => {
            const item = placesData[k];
            return `<div class="rec-card" onclick="window.location.href='detail.html?id=${k}'"><img src="${item.images[0]}"><div class="rec-info"><h4>${item.name}</h4><p>${item.location}</p></div></div>`;
        }).join('');
    }
}
function initHeaderDropdown() {
    const toggle = document.querySelector('.user-profile-toggle');
    const menu = document.querySelector('.user-dropdown-menu');
    if (toggle && menu) {
        toggle.addEventListener('click', (e) => { e.stopPropagation(); menu.classList.toggle('active'); });
        document.addEventListener('click', (e) => { if (!toggle.contains(e.target)) menu.classList.remove('active'); });
    }
}
function checkAuth() {
    const token = localStorage.getItem('token');
    const user = localStorage.getItem('username');
    const unsigned = document.getElementById('unsignedBlock');
    const signed = document.getElementById('signedBlock');
    if (token && user) {
        document.getElementById('displayUsername').textContent = user;
        unsigned.style.display = 'none'; signed.style.display = 'block';
    } else {
        unsigned.style.display = 'flex'; signed.style.display = 'none';
    }
    const logout = document.getElementById('btnLogout');
    if(logout) logout.addEventListener('click', (e) => { e.preventDefault(); localStorage.clear(); window.location.reload(); });
}

// === CHỨC NĂNG TÌM KIẾM (LINK VỀ RESULT PAGE) ===
function handleDetailSearch() {
    const input = document.getElementById('detailSearchInput');
    const query = input.value.trim();
    
    if (query) {
        // Chuyển hướng sang trang results.html kèm từ khóa
        // encodeURIComponent để xử lý các ký tự đặc biệt hoặc tiếng Việt
        window.location.href = `results.html?q=${encodeURIComponent(query)}`;
    } else {
        // Hiệu ứng rung nhẹ hoặc focus nếu người dùng chưa nhập gì (Tùy chọn)
        input.focus();
        input.style.borderBottomColor = "red";
        setTimeout(() => input.style.borderBottomColor = "#ccc", 500);
    }
}