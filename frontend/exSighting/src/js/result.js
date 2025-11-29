const API_BASE = 'http://localhost:8000/api/v1';
let currentK = 9;
let currentQuery = '';
let isLoading = false;
let hasMore = true;

document.addEventListener('DOMContentLoaded', () => {
    checkAuth();
    handleRouting();
    initSortDropdown();
    initInfiniteScroll();
});

// 1. AUTH LOGIC
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

    const logoutBtn = document.getElementById('btnLogout');
    if(logoutBtn) {
        logoutBtn.addEventListener('click', (e) => {
            e.preventDefault();
            localStorage.clear();
            window.location.reload();
        });
    }
}

// 2. ROUTING & DATA FETCHING
function handleRouting() {
    const params = new URLSearchParams(window.location.search);
    const q = params.get('q') || params.get('text') || '';
    
    const input = document.getElementById('resultsPageInput');
    const btn = document.getElementById('resultsPageSearchBtn');

    if(q) input.value = q;
    currentQuery = q;

    // Gọi API Backend
    fetchData(q, currentK, false);

    // Bắt sự kiện tìm kiếm lại
    function doSearch() {
        const val = input.value.trim();
        if(val) {
            currentQuery = val;
            currentK = 9;
            hasMore = true;
            fetchData(val, currentK, false);
        }
    }
    btn.addEventListener('click', doSearch);
    input.addEventListener('keypress', (e) => { if(e.key==='Enter') doSearch(); });
}

async function fetchData(query, topK, isLoadMore = false) {
    if (isLoading) return;
    isLoading = true;

    const grid = document.getElementById('resultsGrid');
    const count = document.getElementById('totalCount');
    
    if (!isLoadMore) {
        grid.innerHTML = '<p style="text-align:center;width:100%;padding:40px;">Loading...</p>';
    }

    try {
        const res = await fetch(`${API_BASE}/recommend`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ 
                user_text: query || "popular places in Vietnam", 
                top_k: topK 
            })
        });

        if (!res.ok) throw new Error(`HTTP ${res.status}`);

        const data = await res.json();
        const items = data.results || [];

        if (!isLoadMore) {
            // Lần đầu load
            count.innerText = items.length;
            renderResults(items);
        } else {
            // Load more: chỉ render items mới
            const oldLength = topK - 9;
            const newItems = items.slice(oldLength);
            
            if (newItems.length === 0) {
                hasMore = false;
            } else {
                count.innerText = items.length;
                renderResults(newItems, true);
            }
        }

    } catch (err) {
        console.error("Fetch error:", err);
        if (!isLoadMore) {
            grid.innerHTML = '<p class="no-result" style="width:100%;text-align:center;padding:40px;">Error connecting to server. Please try again.</p>';
        }
    } finally {
        isLoading = false;
    }
}

function renderResults(items, append = false) {
    const grid = document.getElementById('resultsGrid');
    
    if (!append) {
        grid.innerHTML = '';
    }

    if (items.length === 0 && !append) {
        grid.innerHTML = '<p class="no-result" style="width:100%;text-align:center;padding:40px;">No results found.</p>';
        return;
    }

    items.forEach(item => {
        const card = createResultCard(item);
        grid.appendChild(card);
    });
}

function createResultCard(item) {
    const card = document.createElement('div');
    card.className = 'result-card';

    // Image placeholder - sử dụng ảnh mặc định
    const defaultImages = {
        'beach': 'https://images.unsplash.com/photo-1528127269322-539801943592?q=80&w=2070',
        'mountain': 'https://images.unsplash.com/photo-1599229062397-6c8418047918?q=80&w=2070',
        'island': 'https://images.unsplash.com/photo-1559827260-dc66d52bef19?q=80&w=2070',
        'city': 'https://images.unsplash.com/photo-1557750255-c76072a7aad1?q=80&w=2070',
        'default': 'https://images.unsplash.com/photo-1528127269322-539801943592?q=80&w=2070'
    };

    const themes = item.themes || [];
    let imgSrc = defaultImages.default;
    if (themes.includes('beach')) imgSrc = defaultImages.beach;
    else if (themes.includes('mountain')) imgSrc = defaultImages.mountain;
    else if (themes.includes('island')) imgSrc = defaultImages.island;
    else if (themes.includes('city')) imgSrc = defaultImages.city;

    card.innerHTML = `
        <div class="card-img-top">
            <img src="${imgSrc}" alt="${item.name}">
            <div class="view-badge"><i class="fas fa-star"></i> ${item.score.toFixed(2)}</div>
        </div>
        <div class="card-body">
            <h4 class="card-title">${item.name}</h4>
            <p class="card-subtitle">${item.province || 'Vietnam'}</p>
        </div>
        <div class="card-footer">
            <button class="icon-action like-btn"><i class="fas fa-thumbs-up"></i></button>
            <button class="icon-action dislike-btn"><i class="fas fa-thumbs-down"></i></button>
        </div>
    `;

    return card;
}

// 3. INFINITE SCROLL
function initInfiniteScroll() {
    window.addEventListener('scroll', () => {
        if (isLoading || !hasMore) return;

        if ((window.innerHeight + window.scrollY) >= document.body.offsetHeight - 300) {
            currentK += 9;
            fetchData(currentQuery, currentK, true);
        }
    });
}

// 4. SORT DROPDOWN UI
function initSortDropdown() {
    const dropdown = document.getElementById('customSort');
    const trigger = dropdown.querySelector('.sort-trigger');
    const options = dropdown.querySelectorAll('.sort-option');
    const display = document.getElementById('currentSortValue');

    trigger.addEventListener('click', (e) => {
        e.stopPropagation();
        dropdown.classList.toggle('open');
    });

    options.forEach(opt => {
        opt.addEventListener('click', () => {
            display.innerText = opt.innerText;
            options.forEach(o => o.classList.remove('active'));
            opt.classList.add('active');
            dropdown.classList.remove('open');
            // TODO: Implement sort logic if needed
        });
    });

    document.addEventListener('click', (e) => {
        if(!dropdown.contains(e.target)) dropdown.classList.remove('open');
    });
}






















// document.addEventListener('DOMContentLoaded', () => {
//   // --- CẤU HÌNH API (Sửa 1 chỗ duy nhất tại đây) ---
//   const apiBase = 'http://localhost:8000'; 
  
//   const params  = new URLSearchParams(location.search);
  
//   // Toast notification function - accessible alternative to alert()
//   function showToast(message, type = 'info', duration = 4000) {
//     const container = document.getElementById('toast-container');
//     const toast = document.createElement('div');
//     toast.className = `toast ${type}`;
//     toast.setAttribute('role', 'status');
    
//     const icons = {
//       success: '✓',
//       error: '✕',
//       warning: '⚠',
//       info: 'ℹ'
//     };
    
//     const iconSpan = document.createElement('span');
//     iconSpan.className = 'toast-icon';
//     iconSpan.textContent = icons[type] || icons.info;
    
//     const messageSpan = document.createElement('span');
//     messageSpan.className = 'toast-message';
//     messageSpan.textContent = message;
    
//     const closeBtn = document.createElement('button');
//     closeBtn.className = 'toast-close';
//     closeBtn.setAttribute('aria-label', 'Close notification');
//     closeBtn.textContent = '×';
//     closeBtn.addEventListener('click', () => removeToast(toast));
    
//     toast.appendChild(iconSpan);
//     toast.appendChild(messageSpan);
//     toast.appendChild(closeBtn);
    
//     container.appendChild(toast);
    
//     const timeoutId = setTimeout(() => removeToast(toast), duration);
//     toast._timeoutId = timeoutId;
//   }
  
//   function removeToast(toast) {
//     if (!toast.parentElement) return;
//     if (toast._timeoutId) {
//       clearTimeout(toast._timeoutId);
//     }
//     toast.style.animation = 'fadeOut 0.3s ease-out forwards';
//     setTimeout(() => toast.remove(), 300);
//   }
  
//   // Lấy text tìm kiếm
//   const text = (params.get('text') || '').trim();
  
//   // Khởi tạo số lượng k ban đầu
//   let currentK = Number(params.get('k') || '6');
//   const stepK  = 6; 
  
//   let isLoading = false; 
//   let isFull    = false; 

//   // DOM Elements
//   const headerH2      = document.querySelector('.results-header h2');
//   const cardsContainer= document.querySelector('.cards');
//   const loader        = document.querySelector('.loading-indicator');
//   const headerInput   = document.querySelector('.search-bar input');
//   const headerBtn     = document.querySelector('.search-bar button');

//   if (headerInput) headerInput.value = text;

//   // Hàm tạo thẻ HTML cho 1 địa điểm
//   function renderCard(item){
//     const div = document.createElement('div');
//     div.className = 'card';
//     const img = document.createElement('img');
//     img.src = 'images/halong.jpg'; 
//     img.alt = item.name;
    
//     const name = document.createElement('p'); 
//     name.textContent = item.name;
    
//     const meta = document.createElement('p');
//     meta.style.fontWeight='normal'; 
//     meta.style.color='#666'; 
//     meta.textContent = `${item.province ?? ''} • Score: ${parseFloat(item.score).toFixed(2)}`;

//     const starContainer = document.createElement('div');
//     starContainer.className = 'star-rating';
    
//     for (let i = 1; i <= 5; i++) {
//         const star = document.createElement('span');
//         star.innerHTML = '&#9733;'; 
//         star.className = 'star';
//         star.dataset.value = i; 
//         star.dataset.id = item.id; 
        
//         star.onclick = (e) => handleRating(item.id, i, starContainer);
        
//         starContainer.appendChild(star);
//     }

//     div.append(img, name, meta, starContainer);
//     return div;
//   }

//   // --- HÀM XỬ LÝ ĐÁNH GIÁ ---
//   async function handleRating(placeId, score, container) {
//       const token = localStorage.getItem('token');
//       if (!token) {
//           showToast("Bạn cần đăng nhập để đánh giá!", "warning");
//           window.location.href = "login.html";
//           return;
//       }

//       try {
//           // Đã xóa khai báo apiBase trùng lặp ở đây
//           const res = await fetch(`${apiBase}/api/v1/user/rate`, {
//               method: 'POST',
//               headers: { 
//                   'Content-Type': 'application/json',
//                   'Authorization': `Bearer ${token}`
//               },
//               body: JSON.stringify({ place_id: placeId, score: score })
//           });

//           if (res.ok) {
//               const stars = container.querySelectorAll('.star');
//               stars.forEach((s, index) => {
//                   if (index < score) s.classList.add('active');
//                   else s.classList.remove('active');
//               });
//               showToast(`Đã đánh giá ${score} sao!`, "success");
//           } else {
//               if (res.status === 401) {
//                   showToast("Phiên đăng nhập hết hạn. Vui lòng đăng nhập lại.", "error");
//                   window.location.href = "login.html";
//               } else {
//                   showToast("Có lỗi xảy ra khi gửi đánh giá.", "error");
//               }
//           }
//       } catch (e) {
//           console.error(e);
//           showToast("Không thể kết nối tới server.", "error");
//       }
//   }

//   // Hàm gọi API chính
//   async function fetchResults(kValue, isLoadMore = false) {
//     if (!text) {
//       headerH2.textContent = '0 results';
//       return;
//     }
    
//     if (!isLoadMore) {
//       headerH2.textContent = 'Loading...';
//       cardsContainer.innerHTML = ''; 
//     } else {
//       loader.classList.add('active'); 
//     }

//     isLoading = true;

//     try {
//       // Sử dụng apiBase chung
//       const r = await fetch(`${apiBase}/api/v1/recommend`, {
//         method: 'POST',
//         headers: { 'Content-Type': 'application/json' },
//         body: JSON.stringify({ user_text: text, top_k: kValue })
//       });

//       if (!r.ok) throw new Error(`HTTP ${r.status}`);

//       const data = await r.json();
//       const items = data.results || [];

//       if (!isLoadMore) {
//         headerH2.textContent = `${items.length} results`;
//         items.forEach(it => cardsContainer.appendChild(renderCard(it)));
//       } else {
//         const oldLength = currentK - stepK; 
//         const newItems = items.slice(oldLength); 

//         if (newItems.length === 0) {
//           isFull = true; 
//           loader.textContent = "Đã hiển thị hết kết quả.";
//         } else {
//           newItems.forEach(it => cardsContainer.appendChild(renderCard(it)));
//           headerH2.textContent = `${items.length} results`; 
//         }
//       }

//     } catch (e) {
//       console.error(e);
//       if (!isLoadMore) {
//         headerH2.textContent = 'Error loading data';
//         cardsContainer.innerHTML = `<div style="color:red; padding:10px">${e.message}</div>`;
//       }
//     } finally {
//       isLoading = false;
//       loader.classList.remove('active');
//     }
//   }

//   // --- HÀM MỚI: Tải lại lịch sử đánh giá ---
//   async function loadUserRatings() {
//       const token = localStorage.getItem('token');
//       if (!token) return;

//       try {
//           // Đã xóa khai báo apiBase trùng lặp ở đây
//           const res = await fetch(`${apiBase}/api/v1/user/my-ratings`, {
//               method: 'GET',
//               headers: { 
//                   'Authorization': `Bearer ${token}`
//               }
//           });

//           if (res.ok) {
//               const ratingsMap = await res.json(); 
              
//               document.querySelectorAll('.star-rating').forEach(container => {
//                   const firstStar = container.querySelector('.star');
//                   if (!firstStar) return;
                  
//                   const placeId = firstStar.dataset.id;
                  
//                   if (ratingsMap[placeId]) {
//                       const userScore = ratingsMap[placeId];
//                       const stars = container.querySelectorAll('.star');
//                       stars.forEach((s, index) => {
//                           if (index < userScore) s.classList.add('active');
//                           else s.classList.remove('active');
//                       });
//                   }
//               });
//           }
//       } catch (e) {
//           console.error("Lỗi tải lịch sử đánh giá:", e);
//       }
//   }

//   // Chạy lần đầu tiên
//   (async () => {
//         await fetchResults(currentK, false);
//         await loadUserRatings();
//     })();

//   window.addEventListener('scroll', () => {
//     if (isLoading || isFull) return;
//     if ((window.innerHeight + window.scrollY) >= document.body.offsetHeight - 100) {
//       currentK += stepK; 
//       fetchResults(currentK, true); 
//     }
//   });

//   function triggerSearch() {
//     const q = (headerInput?.value || '').trim();
//     if (!q) return;
//     const newParams = new URLSearchParams();
//     newParams.set('text', q);
//     newParams.set('k', '6'); 
//     window.location.search = newParams.toString();
//   }

//   headerBtn?.addEventListener('click', triggerSearch);
//   headerInput?.addEventListener('keydown', (e) => {
//     if (e.key === 'Enter') triggerSearch();
//   });
// });