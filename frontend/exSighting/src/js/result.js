import { CONFIG } from './config.js';
import { getUserLocationWithCache, formatDistance, isGeolocationSupported, calculateDistance } from './gps-utils.js';

// Biến theo dõi phân trang và trạng thái
let currentPage = 0;
let isLoading = false;
let hasMore = true;
let currentQuery = "";
const ITEMS_PER_PAGE = 20;
let allLoadedResults = []; // Lưu tất cả kết quả đã load
let currentSortMode = 'newest'; // Track current sort mode

document.addEventListener('DOMContentLoaded', () => {
    // Apply saved theme
    const savedTheme = localStorage.getItem('theme') || 'light';
    if (savedTheme === 'dark') {
        document.body.classList.add('dark-mode');
    }
    
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
    const mode = params.get('mode') || ""; // Lấy mode từ URL
    
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
        let allResults = [];
        
        // CHIẾN LƯỢC TÌM KIẾM KẾT HỢP:
        // 1. Nếu có query -> tìm theo TÊN địa điểm trước
        // 2. Sau đó tìm theo SEMANTIC (từ khóa)
        // 3. Merge và loại bỏ duplicate
        
        if (query && query.trim()) {
            // 1. Tìm theo tên địa điểm
            const nameResults = await searchByName(query);
            
            // 2. Tìm theo semantic/từ khóa
            const semanticResults = await searchBySemantic(query);
            
            // 3. Merge results (ưu tiên name search trước)
            const seenIds = new Set();
            
            // Thêm kết quả tìm theo tên trước
            nameResults.forEach(place => {
                if (!seenIds.has(place.id)) {
                    allResults.push({...place, score: 10.0}); // Boost score cho exact name match
                    seenIds.add(place.id);
                }
            });
            
            // Thêm kết quả semantic, loại bỏ duplicate
            semanticResults.forEach(place => {
                if (!seenIds.has(place.id)) {
                    allResults.push(place);
                    seenIds.add(place.id);
                }
            });
        } else {
            // Không có query -> chỉ dùng semantic (recommend general)
            allResults = await searchBySemantic("");
        }
        
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

// === HELPER FUNCTIONS ĐỂ TÌM KIẾM ===

// Tìm kiếm theo tên địa điểm (exact/partial match)
async function searchByName(query) {
    try {
        const response = await fetch(
            `${CONFIG.apiBase}/api/v1/place/search/by-name?q=${encodeURIComponent(query)}&limit=50`
        );
        
        if (!response.ok) {
            console.error('Name search failed');
            return [];
        }
        
        const places = await response.json();
        return places || [];
    } catch (error) {
        console.error('Error searching by name:', error);
        return [];
    }
}

// Tìm kiếm theo semantic/từ khóa (dùng recommend API)
async function searchBySemantic(query) {
    try {
        const token = localStorage.getItem('token');
        const headers = {
            'Content-Type': 'application/json'
        };
        
        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }
        
        const userText = query || "Vietnam travel";
        
        const response = await fetch(`${CONFIG.apiBase}/api/v1/recommend`, {
            method: 'POST',
            headers: headers,
            body: JSON.stringify({
                user_text: userText,
                top_k: 100
            })
        });
        
        if (!response.ok) {
            console.error('Semantic search failed');
            return [];
        }
        
        const data = await response.json();
        return data.results || [];
    } catch (error) {
        console.error('Error searching by semantic:', error);
        return [];
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
            
            // Get province - fallback chain: province -> tags[0] -> 'Vietnam'
            const province = item.province || (item.tags && item.tags.length > 0 ? item.tags[0] : 'Vietnam');
            
            // Show distance if available
            const distanceBadge = item.distance !== undefined 
                ? `<div class="distance-badge"><i class="fas fa-map-marker-alt"></i> ${formatDistance(item.distance)}</div>` 
                : '';
            
            return `
            <div class="result-card" onclick="goToDetail(${item.id})" style="cursor: pointer;">
                <div class="card-img-top">
                    <img src="${imgSrc}" alt="${item.name}" onerror="this.src='https://images.unsplash.com/photo-1528127269322-539801943592?q=80&w=2070';">
                    <div class="view-badge"><i class="fas fa-star"></i> ${scoreDisplay}</div>
                    ${distanceBadge}
                </div>
                <div class="card-body">
                    <h4 class="card-title">${item.name}</h4>
                    <p class="card-subtitle">${province}</p>
                </div>
                <div class="card-footer">
                    <button class="icon-action like-btn" data-place-id="${item.id}" onclick="handleLike(event, ${item.id})"><i class="far fa-thumbs-up"></i></button>
                    <button class="icon-action dislike-btn" data-place-id="${item.id}" onclick="handleDislike(event, ${item.id})"><i class="far fa-thumbs-down"></i></button>
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
        
        // Check và update trạng thái like/dislike cho tất cả places
        updateAllLikeStatus();
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
    await togglePlaceLike(event, placeId, true);
};

window.handleDislike = async function(event, placeId) {
    event.stopPropagation();
    await togglePlaceLike(event, placeId, false);
};

// Update all like/dislike status for places in result page
async function updateAllLikeStatus() {
    const token = localStorage.getItem('token');
    if (!token) return; // Không login thì không cần check
    
    // Lấy tất cả các nút like/dislike
    const likeButtons = document.querySelectorAll('.like-btn');
    const dislikeButtons = document.querySelectorAll('.dislike-btn');
    
    // Tạo Map để lưu buttons theo placeId
    const buttonsByPlace = new Map();
    
    likeButtons.forEach(btn => {
        const placeId = btn.dataset.placeId;
        if (!buttonsByPlace.has(placeId)) {
            buttonsByPlace.set(placeId, { like: null, dislike: null });
        }
        buttonsByPlace.get(placeId).like = btn;
    });
    
    dislikeButtons.forEach(btn => {
        const placeId = btn.dataset.placeId;
        if (!buttonsByPlace.has(placeId)) {
            buttonsByPlace.set(placeId, { like: null, dislike: null });
        }
        buttonsByPlace.get(placeId).dislike = btn;
    });
    
    // Check status cho từng place
    for (const [placeId, buttons] of buttonsByPlace.entries()) {
        try {
            const response = await fetch(`${CONFIG.apiBase}/api/v1/likes/check/place/${placeId}`, {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });
            
            if (response.ok) {
                const data = await response.json();
                updatePlaceLikeButtonsUI(buttons.like, buttons.dislike, data.status);
            }
        } catch (error) {
            console.error(`Error checking like status for place ${placeId}:`, error);
        }
    }
}

// Update UI cho một cặp nút like/dislike
function updatePlaceLikeButtonsUI(likeBtn, dislikeBtn, status) {
    if (!likeBtn || !dislikeBtn) return;
    
    // Reset both buttons
    const likeIcon = likeBtn.querySelector('i');
    const dislikeIcon = dislikeBtn.querySelector('i');
    
    if (likeIcon) likeIcon.className = 'far fa-thumbs-up';
    if (dislikeIcon) dislikeIcon.className = 'far fa-thumbs-down';
    likeBtn.style.color = '';
    dislikeBtn.style.color = '';
    
    // Apply style based on status
    if (status === 'liked') {
        if (likeIcon) likeIcon.className = 'fas fa-thumbs-up';
        likeBtn.style.color = '#14838B'; // Teal
    } else if (status === 'disliked') {
        if (dislikeIcon) dislikeIcon.className = 'fas fa-thumbs-down';
        dislikeBtn.style.color = '#e74c3c'; // Red
    }
    // else neutral - keep default outline style
}


// Toast notification helper (copied from detail.js)
let toastTimeout;
let keyListener;
function showToast(message, type = 'success') {
    let toast = document.getElementById('toast');
    let toastMessage = document.getElementById('toastMessage');
    let icon = toast && toast.querySelector('i');
    
    if (!toast || !toastMessage || !icon) return;
    
    // --- FIX: Xóa display none nếu có ---
    toast.style.display = 'flex'; 
    // ------------------------------------

    if (toastTimeout) clearTimeout(toastTimeout);
    if (keyListener) document.removeEventListener('keydown', keyListener);
    
    toastMessage.textContent = message;
    
    // Cập nhật icon và màu sắc
    if (type === 'success') {
        icon.className = 'fas fa-check-circle';
        toast.style.background = 'linear-gradient(135deg, #14838B 0%, #0d5f66 100%)';
    } else if (type === 'error') {
        icon.className = 'fas fa-exclamation-circle';
        toast.style.background = 'linear-gradient(135deg, #e74c3c 0%, #c0392b 100%)';
    } else if (type === 'warning') {
        icon.className = 'fas fa-info-circle';
        toast.style.background = 'linear-gradient(135deg, #f39c12 0%, #e67e22 100%)';
    }
    
    toast.classList.remove('hide');
    toast.classList.add('show');
    
    toastTimeout = setTimeout(() => { hideToast(); }, 3000); // 3 giây
    
    keyListener = (e) => { hideToast(); };
    document.addEventListener('keydown', keyListener, { once: true });
}

function hideToast() {
    let toast = document.getElementById('toast');
    if (!toast) return;
    
    toast.classList.add('hide');
    
    setTimeout(() => { 
        toast.classList.remove('show', 'hide'); 
        // Ẩn hẳn đi sau khi animation kết thúc để tránh che các nút khác
        toast.style.display = 'none'; 
    }, 400);
    
    if (toastTimeout) clearTimeout(toastTimeout);
    if (keyListener) document.removeEventListener('keydown', keyListener);
}

// Like/Dislike logic for places
async function togglePlaceLike(event, placeId, isLike) {
    const token = localStorage.getItem('token');
    if (!token) {
        showToast('Please login to interact with places!', 'warning');
        setTimeout(() => {
            localStorage.setItem('returnUrl', window.location.href);
            window.location.href = 'login.html';
        }, 1500);
        return;
    }
    try {
        const btn = event.target.closest('button');
        
        const response = await fetch(`${CONFIG.apiBase}/api/v1/likes/place`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({ 
                place_id: parseInt(placeId),
                is_like: isLike
            })
        });
        
        if (response.ok) {
            const result = await response.json();
            
            // Tìm cả 2 nút like và dislike của place này
            const cardFooter = btn ? btn.closest('.card-footer') : null;
            let likeBtn = null;
            let dislikeBtn = null;
            
            if (cardFooter) {
                likeBtn = cardFooter.querySelector('.like-btn');
                dislikeBtn = cardFooter.querySelector('.dislike-btn');
            }
            
            // Update UI cho cả 2 nút
            if (likeBtn && dislikeBtn) {
                updatePlaceLikeButtonsUI(likeBtn, dislikeBtn, result.status);
            }
            
            if (result.action === "removed") {
                showToast(isLike ? 'Like removed' : 'Dislike removed', 'warning');
            } else if (result.action === "created") {
                showToast(isLike ? '✓ Place liked!' : 'Place disliked', isLike ? 'success' : 'warning');
            } else if (result.action === "updated") {
                showToast(isLike ? 'Changed to like!' : 'Changed to dislike', 'success');
            }
        } else if (response.status === 401) {
            showToast('Session expired. Please login again.', 'error');
            setTimeout(() => {
                localStorage.clear();
                localStorage.setItem('returnUrl', window.location.href);
                window.location.href = 'login.html';
            }, 2000);
        }
    } catch (error) {
        console.error('Error toggling place like:', error);
        showToast('Failed to update like status', 'error');
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
        opt.onclick = async () => {
            const sortValue = opt.getAttribute('data-value');
            
            if(display) display.innerText = opt.innerText;
            options.forEach(o => o.classList.remove('active'));
            opt.classList.add('active');
            dropdown.classList.remove('open');
            
            // Handle sorting
            currentSortMode = sortValue;
            
            if (sortValue === 'nearby') {
                await sortByDistance();
            } else {
                // Other sort modes - reload with normal API
                currentPage = 0;
                allLoadedResults = [];
                hasMore = true;
                fetchAndDisplayResults();
            }
        };
    });

    document.onclick = (e) => {
        if(!dropdown.contains(e.target)) dropdown.classList.remove('open');
    };
}

// === SORT BY DISTANCE (GPS-BASED) ===
// Sort kết quả hiện tại theo khoảng cách từ vị trí người dùng
async function sortByDistance() {
    // Check if geolocation is supported
    if (!isGeolocationSupported()) {
        showToast('Your browser does not support GPS location', 'error');
        return;
    }
    
    // Check if we have results to sort
    if (allLoadedResults.length === 0) {
        showToast('No results to sort', 'warning');
        return;
    }
    
    const grid = document.getElementById('resultsGrid');
    const count = document.getElementById('totalCount');
    
    // Show loading
    if (grid) {
        grid.innerHTML = `
            <div style="grid-column: 1/-1; text-align: center; padding: 50px;">
                <i class="fas fa-spinner fa-spin" style="font-size: 2rem; color: #4A90E2;"></i>
                <p style="margin-top: 20px; color: #666;">Getting your location...</p>
            </div>
        `;
    }
    
    try {
        // Get user location (with cache)
        const userLocation = await getUserLocationWithCache();
        console.log('📍 User location:', userLocation);
        
        // Tính khoảng cách cho mỗi địa điểm trong kết quả hiện tại
        const resultsWithDistance = allLoadedResults.map(place => {
            // Lấy lat/lon từ place (nếu có)
            const placeLat = place.lat;
            const placeLon = place.lon;
            
            let distance = null;
            if (placeLat && placeLon) {
                distance = calculateDistance(
                    userLocation.lat, 
                    userLocation.lon, 
                    placeLat, 
                    placeLon
                );
            }
            
            return {
                ...place,
                distance: distance
            };
        });
        
        // Sort theo khoảng cách (gần nhất trước)
        // Các địa điểm không có tọa độ sẽ được đưa xuống cuối
        resultsWithDistance.sort((a, b) => {
            if (a.distance === null && b.distance === null) return 0;
            if (a.distance === null) return 1;
            if (b.distance === null) return -1;
            return a.distance - b.distance;
        });
        
        console.log(`✅ Sorted ${resultsWithDistance.length} results by distance`);
        
        // Update allLoadedResults với distance đã tính
        allLoadedResults = resultsWithDistance;
        currentPage = 0;
        hasMore = false;
        
        // Render tất cả kết quả đã sort
        renderResults(resultsWithDistance, '', grid, count, false);
        
        if (count) count.innerText = resultsWithDistance.length;
        
        // Hiển thị thông báo
        const nearbyCount = resultsWithDistance.filter(p => p.distance !== null).length;
        if (nearbyCount > 0) {
            const closestPlace = resultsWithDistance[0];
            const closestDistance = closestPlace.distance ? formatDistance(closestPlace.distance) : 'N/A';
            showToast(`Sorted by distance. Closest: ${closestDistance}`, 'success');
        } else {
            showToast('Sorted results (location data unavailable for some places)', 'warning');
        }
        
    } catch (error) {
        console.error('Error sorting by distance:', error);
        
        let errorMessage = 'Unable to get your location';
        if (error.message.includes('denied')) {
            errorMessage = 'Location access denied. Please enable location permission in your browser settings.';
        }
        
        showToast(errorMessage, 'error');
        
        // Fallback: re-render kết quả hiện tại
        renderResults(allLoadedResults, '', grid, count, false);
    }
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