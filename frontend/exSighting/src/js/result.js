import { CONFIG } from './config.js';

// Biến theo dõi phân trang và trạng thái
let currentPage = 0;
let isLoading = false;
let hasMore = true;
let currentQuery = "";
const ITEMS_PER_PAGE = 20;
let allLoadedResults = []; // Lưu tất cả kết quả đã load

document.addEventListener('DOMContentLoaded', () => {
    checkAuth();
    
    // Khởi tạo chức năng tìm kiếm ngay khi trang load
    handleResultPageSearch(); 
    
    // --- GỌI API ĐỂ LẤY KẾT QUẢ ---
    fetchAndDisplayResults();

    initSortDropdown();
    
    // Thêm infinite scroll listener
    initInfiniteScroll();
});

// === HÀM GỌI API VÀ HIỂN THỊ KẾT QUẢ ===
async function fetchAndDisplayResults(isLoadMore = false) {
    const grid = document.getElementById('resultsGrid');
    const count = document.getElementById('totalCount');
    const params = new URLSearchParams(window.location.search);
    const query = params.get('q') || "";
    
    // Nếu query thay đổi, reset tất cả
    if (query !== currentQuery) {
        currentQuery = query;
        currentPage = 0;
        allLoadedResults = [];
        hasMore = true;
        if (grid) grid.innerHTML = '';
    }
    
    // Ngăn multiple requests cùng lúc
    if (isLoading || !hasMore) return;
    isLoading = true;
    
    // Hiển thị loading
    if (grid && !isLoadMore) {
        grid.innerHTML = '<p style="grid-column: 1/-1; text-align: center; margin-top: 50px;">Loading...</p>';
    } else if (grid && isLoadMore) {
        // Thêm loading indicator khi load more
        const loadingDiv = document.createElement('div');
        loadingDiv.id = 'loadingMore';
        loadingDiv.style.cssText = 'grid-column: 1/-1; text-align: center; padding: 20px;';
        loadingDiv.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Loading more...';
        grid.appendChild(loadingDiv);
    }
    
    try {
        // Gọi API recommendation với user_text
        const token = localStorage.getItem('token');
        const headers = {
            'Content-Type': 'application/json'
        };
        
        // Thêm token nếu user đã đăng nhập
        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }
        
        // Tăng top_k để lấy nhiều kết quả hơn
        const response = await fetch(`${CONFIG.apiBase}/api/v1/recommend`, {
            method: 'POST',
            headers: headers,
            body: JSON.stringify({
                user_text: query || "Vietnam travel",
                top_k: 100 // Lấy 100 kết quả từ backend
            })
        });
        
        if (!response.ok) {
            throw new Error('Failed to fetch recommendations');
        }
        
        const data = await response.json();
        const allResults = data.results || [];
        
        // Lưu tất cả kết quả và render theo trang
        if (!isLoadMore) {
            allLoadedResults = allResults;
            currentPage = 0;
        }
        
        // Tính toán kết quả cho trang hiện tại
        const startIdx = currentPage * ITEMS_PER_PAGE;
        const endIdx = startIdx + ITEMS_PER_PAGE;
        const pageResults = allLoadedResults.slice(startIdx, endIdx);
        
        // Kiểm tra còn kết quả không
        hasMore = endIdx < allLoadedResults.length;
        
        // Remove loading indicator if exists
        const loadingMore = document.getElementById('loadingMore');
        if (loadingMore) loadingMore.remove();
        
        // Render kết quả
        renderResults(pageResults, query, grid, count, isLoadMore);
        
        // Tăng page counter
        currentPage++;
        
    } catch (error) {
        console.error('Error fetching results:', error);
        if (grid && !isLoadMore) {
            grid.innerHTML = `<p style="grid-column: 1/-1; text-align: center; color: #e74c3c; margin-top: 50px;">
                Failed to load recommendations. Please try again later.
            </p>`;
        }
        hasMore = false;
    } finally {
        isLoading = false;
    }
}

// === HÀM RENDER KẾT QUẢ ===
function renderResults(results, query, grid, count, isLoadMore = false) {
    if (!grid) return;
    
    // Cập nhật số lượng tổng
    if (count) count.innerText = allLoadedResults.length;
    
    if (results.length === 0 && !isLoadMore) {
        grid.innerHTML = `<p style="grid-column: 1/-1; text-align: center; font-size: 1.2rem; color: #666; margin-top: 50px;">
            No results found${query ? ` for "<b>${query}</b>"` : ''}. 
        </p>`;
    } else {
        // Tạo HTML danh sách
        const htmlContent = results.map(item => {
            // Lấy ảnh thực từ item.image
            let imgSrc = "https://images.unsplash.com/photo-1528127269322-539801943592?q=80&w=2070"; // Mặc định
            
            if (item.image && Array.isArray(item.image) && item.image.length > 0) {
                imgSrc = item.image[0]; // Lấy ảnh đầu tiên
            } else if (item.themes && item.themes.length > 0) {
                // Fallback: chọn ảnh dựa trên themes nếu không có ảnh
                const theme = item.themes[0].toLowerCase();
                if (theme.includes('mountain') || theme.includes('núi')) {
                    imgSrc = "https://images.unsplash.com/photo-1599229062397-6c8418047918?q=80&w=2070";
                } else if (theme.includes('city') || theme.includes('thành phố') || theme.includes('historical')) {
                    imgSrc = "https://images.unsplash.com/photo-1557750255-c76072a7aad1?q=80&w=2070";
                } else if (theme.includes('temple') || theme.includes('chùa')) {
                    imgSrc = "https://images.unsplash.com/photo-1548013146-72479768bada?q=80&w=2070";
                }
            }

            // Format score to 1 decimal place
            const scoreDisplay = item.score ? item.score.toFixed(1) : '0.0';
            
            return `
            <div class="result-card" onclick="goToDetail(${item.id})" style="cursor: pointer;">
                <div class="card-img-top">
                    <img src="${imgSrc}" alt="${item.name}" onerror="this.src='https://images.unsplash.com/photo-1528127269322-539801943592?q=80&w=2070';">
                    <div class="view-badge"><i class="fas fa-star"></i> ${scoreDisplay}</div>
                </div>
                <div class="card-body">
                    <h4 class="card-title">${item.name}</h4>
                    <p class="card-subtitle">${item.province || 'Vietnam'}</p>
                </div>
                <div class="card-footer">
                    <button class="icon-action like-btn" onclick="handleLike(event, ${item.id})"><i class="fas fa-thumbs-up"></i></button>
                    <button class="icon-action dislike-btn" onclick="handleDislike(event, ${item.id})"><i class="fas fa-thumbs-down"></i></button>
                </div>
            </div>
            `;
        }).join('');
        
        if (isLoadMore) {
            // Append thêm vào grid hiện tại
            grid.insertAdjacentHTML('beforeend', htmlContent);
        } else {
            // Thay thế toàn bộ
            grid.innerHTML = htmlContent;
        }
    }
}

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

// === HÀM XỬ LÝ LIKE/DISLIKE ===
window.handleLike = async function(event, placeId) {
    event.stopPropagation();
    await submitRating(placeId, 'like');
};

window.handleDislike = async function(event, placeId) {
    event.stopPropagation();
    await submitRating(placeId, 'dislike');
};

async function submitRating(placeId, interactionType) {
    const token = localStorage.getItem('token');
    
    if (!token) {
        alert('Please login to rate places!');
        window.location.href = 'login.html';
        return;
    }
    
    try {
        const response = await fetch(`${CONFIG.apiBase}/api/v1/rating`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({
                place_id: placeId,
                interaction_type: interactionType
            })
        });
        
        if (response.ok) {
            // Show success feedback
            const btn = event.target.closest('button');
            if (btn) {
                btn.style.color = interactionType === 'like' ? '#2ecc71' : '#e74c3c';
                setTimeout(() => { btn.style.color = ''; }, 1000);
            }
        } else {
            console.error('Failed to submit rating');
        }
    } catch (error) {
        console.error('Error submitting rating:', error);
    }
}

function checkAuth() {
    const token = localStorage.getItem('token');
    const user = localStorage.getItem('username');
    const unsigned = document.getElementById('unsignedBlock');
    const signed = document.getElementById('signedBlock');
    const headerAvatarContainer = document.getElementById('headerAvatarContainer');
    
    if (token && user) {
        const displayName = localStorage.getItem('displayName') || user;
        const nameDisplay = document.getElementById('displayUsername');
        if(nameDisplay) nameDisplay.textContent = displayName;
        if(unsigned) unsigned.style.display = 'none';
        if(signed) signed.style.display = 'flex';
        
        // Load avatar
        if (headerAvatarContainer) {
            const avatarUrl = localStorage.getItem('avatarUrl');
            if (avatarUrl) {
                const fullAvatarUrl = avatarUrl.startsWith('http') ? avatarUrl : `${CONFIG.apiBase}${avatarUrl}`;
                headerAvatarContainer.innerHTML = `<img src="${fullAvatarUrl}" alt="Avatar" style="width: 100%; height: 100%; border-radius: 50%; object-fit: cover;">`;
            }
        }
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

// === HÀM INFINITE SCROLL ===
function initInfiniteScroll() {
    let scrollTimeout;
    
    window.addEventListener('scroll', () => {
        // Debounce scroll event
        clearTimeout(scrollTimeout);
        scrollTimeout = setTimeout(() => {
            // Kiểm tra nếu đã scroll gần cuối trang
            const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
            const windowHeight = window.innerHeight;
            const documentHeight = document.documentElement.scrollHeight;
            
            // Khi còn 300px nữa là đến cuối trang
            if (scrollTop + windowHeight >= documentHeight - 300) {
                if (!isLoading && hasMore) {
                    fetchAndDisplayResults(true); // Load more
                }
            }
        }, 100); // Debounce 100ms
    });
}