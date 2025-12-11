// === 1. IMPORT CONFIG ===
import { CONFIG } from './config.js';

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

// === 5. KHỞI TẠO & GỌI API ===
document.addEventListener('DOMContentLoaded', async () => {
    checkAuth();
    initHeaderDropdown();

    const params = new URLSearchParams(window.location.search);
    const id = params.get('id'); 
    
    if (!id) {
        // Nếu không có ID, chuyển về trang results
        window.location.href = 'results.html';
        return;
    }
    
    try {
        // Gọi API lấy thông tin địa điểm
        const response = await fetch(`${CONFIG.apiBase}/api/v1/place/${id}`);
        
        if (!response.ok) {
            throw new Error('Place not found');
        }
        
        const placeData = await response.json();
        
        // Xử lý dữ liệu từ backend
        const data = {
            name: placeData.name || 'Unknown',
            location: placeData.tags && placeData.tags.length > 0 ? placeData.tags[0] : 'Vietnam',
            distance: Math.floor(Math.random() * 500 + 50), // Random distance (có thể tính thật từ GPS)
            desc: formatDescription(placeData.description),
            images: placeData.image && placeData.image.length > 0 
                ? placeData.image 
                : ['https://images.unsplash.com/photo-1528127269322-539801943592?q=80&w=2070'],
            tags: placeData.tags || [],
            reviews: [] // Reviews có thể lấy từ comment table sau
        };
        
        currentImagesList = data.images;
        renderPage(data);
        renderRecs(id);
        
        // Load và setup comments
        loadComments(id);
        setupCommentForm(id);
        setupPlaceLikeButtons(id);
        
    } catch (error) {
        console.error('Error loading place details:', error);
        const titleEl = document.getElementById('detailTitle');
        if (titleEl) {
            titleEl.innerHTML = `
                <div style="text-align: center; color: #e74c3c;">
                    <h2>Place not found</h2>
                    <button onclick="window.location.href='home.html'" style="margin-top: 20px; padding: 10px 20px; background: #3498db; color: white; border: none; border-radius: 5px; cursor: pointer;">
                        Back to Home
                    </button>
                </div>
            `;
        }
    }

    // Bàn phím
    document.addEventListener('keydown', (e) => {
        if (e.key === 'ArrowRight') { e.preventDefault(); window.slideThumbs(1); }
        else if (e.key === 'ArrowLeft') { e.preventDefault(); window.slideThumbs(-1); }
    });
});

// Hàm format description từ array thành HTML
function formatDescription(descArray) {
    if (!descArray || descArray.length === 0) {
        return 'No description available.';
    }
    
    // Nếu là array, join thành paragraphs
    if (Array.isArray(descArray)) {
        return descArray.map(para => `<p>${para}</p>`).join('<br>');
    }
    
    return descArray;
}

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

    // Không render reviews ở đây nữa, sẽ load riêng qua loadComments()
}

// === RECOMMENDATION CAROUSEL WITH INFINITE SCROLL ===
let recPage = 0;
let recIsLoading = false;
let recHasMore = true;
let recCurrentPlaceId = null;
const REC_ITEMS_PER_PAGE = 6;

async function renderRecs(currentId) {
    recCurrentPlaceId = currentId;
    recPage = 0;
    recHasMore = true;
    
    const list = document.getElementById('recommendationList');
    if (!list) return;
    
    list.innerHTML = ''; // Clear existing
    
    // Load first batch
    await loadMoreRecommendations();
    
    // Setup scroll listener
    initRecommendationScroll();
    
    // Setup navigation buttons
    setupRecNavigationButtons();
}

async function loadMoreRecommendations() {
    if (recIsLoading || !recHasMore) return;
    
    const list = document.getElementById('recommendationList');
    const loadingIndicator = document.getElementById('recLoadingIndicator');
    
    if (!list) return;
    
    recIsLoading = true;
    if (loadingIndicator) loadingIndicator.style.display = 'block';
    
    try {
        const token = localStorage.getItem('token');
        const headers = {
            'Content-Type': 'application/json'
        };
        
        // Thêm token nếu user đã login để backend recommend dựa trên preferences
        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }
        
        // Gọi API với user_text rỗng để backend sử dụng user preferences
        const response = await fetch(`${CONFIG.apiBase}/api/v1/recommend`, {
            method: 'POST',
            headers: headers,
            body: JSON.stringify({
                user_text: token ? "" : "Vietnam tourism", // Rỗng nếu có token để dùng preferences
                top_k: 50 // Lấy nhiều để có đủ recommendations
            })
        });
        
        if (response.ok) {
            const data = await response.json();
            // Filter out current place và những place đã hiển thị
            const existingIds = Array.from(list.querySelectorAll('.rec-card')).map(
                card => card.dataset.placeId
            );
            
            const newRecommendations = data.results
                .filter(item => 
                    item.id.toString() !== recCurrentPlaceId && 
                    !existingIds.includes(item.id.toString())
                )
                .slice(recPage * REC_ITEMS_PER_PAGE, (recPage + 1) * REC_ITEMS_PER_PAGE);
            
            if (newRecommendations.length === 0) {
                recHasMore = false;
            } else {
                appendRecommendations(newRecommendations);
                recPage++;
            }
        }
    } catch (error) {
        console.error('Error loading recommendations:', error);
        recHasMore = false;
    } finally {
        recIsLoading = false;
        if (loadingIndicator) loadingIndicator.style.display = 'none';
    }
}

function appendRecommendations(recommendations) {
    const list = document.getElementById('recommendationList');
    if (!list) return;
    
    const html = recommendations.map(item => {
        let imgSrc = "https://images.unsplash.com/photo-1528127269322-539801943592?q=80&w=2070";
        
        if (item.image && Array.isArray(item.image) && item.image.length > 0) {
            imgSrc = item.image[0];
        }
        
        return `<div class="rec-card" data-place-id="${item.id}" onclick="window.location.href='detail.html?id=${item.id}'">
            <img src="${imgSrc}" alt="${item.name}">
            <div class="rec-info">
                <h4>${item.name}</h4>
                <p>${item.province || 'Vietnam'}</p>
            </div>
        </div>`;
    }).join('');
    
    list.insertAdjacentHTML('beforeend', html);
}

function initRecommendationScroll() {
    const viewport = document.getElementById('recommendationViewport');
    if (!viewport) return;
    
    let scrollTimeout;
    
    viewport.addEventListener('scroll', () => {
        clearTimeout(scrollTimeout);
        scrollTimeout = setTimeout(() => {
            const scrollLeft = viewport.scrollLeft;
            const scrollWidth = viewport.scrollWidth;
            const clientWidth = viewport.clientWidth;
            
            // Load more khi còn 300px nữa là scroll hết
            if (scrollLeft + clientWidth >= scrollWidth - 300) {
                loadMoreRecommendations();
            }
        }, 100);
    });
}

function setupRecNavigationButtons() {
    const prevBtn = document.getElementById('recPrevBtn');
    const nextBtn = document.getElementById('recNextBtn');
    const viewport = document.getElementById('recommendationViewport');
    
    if (!prevBtn || !nextBtn || !viewport) return;
    
    // Scroll by viewport width
    prevBtn.addEventListener('click', () => {
        viewport.scrollBy({
            left: -viewport.clientWidth * 0.8,
            behavior: 'smooth'
        });
    });
    
    nextBtn.addEventListener('click', () => {
        viewport.scrollBy({
            left: viewport.clientWidth * 0.8,
            behavior: 'smooth'
        });
    });
    
    // Update button states on scroll
    viewport.addEventListener('scroll', () => {
        prevBtn.disabled = viewport.scrollLeft <= 0;
        nextBtn.disabled = viewport.scrollLeft + viewport.clientWidth >= viewport.scrollWidth - 1;
    });
    
    // Initial state
    prevBtn.disabled = true;
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
    const headerAvatarContainer = document.getElementById('headerAvatarContainer');
    
    if (token && user) {
        const displayName = localStorage.getItem('displayName') || user;
        document.getElementById('displayUsername').textContent = displayName;
        unsigned.style.display = 'none'; 
        signed.style.display = 'block';
        
        // Load avatar
        if (headerAvatarContainer) {
            const avatarUrl = localStorage.getItem('avatarUrl');
            if (avatarUrl) {
                const fullAvatarUrl = avatarUrl.startsWith('http') ? avatarUrl : `${CONFIG.apiBase}${avatarUrl}`;
                headerAvatarContainer.innerHTML = `<img src="${fullAvatarUrl}" alt="Avatar" style="width: 100%; height: 100%; border-radius: 50%; object-fit: cover;">`;
            }
        }
    } else {
        unsigned.style.display = 'flex'; 
        signed.style.display = 'none';
    }
    
    const logout = document.getElementById('btnLogout');
    if(logout) logout.addEventListener('click', (e) => { 
        e.preventDefault(); 
        localStorage.clear(); 
        window.location.reload(); 
    });
}

// === CHỨC NĂNG TÌM KIẾM (LINK VỀ RESULT PAGE) ===
window.handleDetailSearch = function() {
    const input = document.getElementById('detailSearchInput');
    const query = input.value.trim();
    
    if (query) {
        // Chuyển hướng sang trang results.html kèm từ khóa - giống như search từ home
        window.location.href = `results.html?q=${encodeURIComponent(query)}`;
    } else {
        // Hiệu ứng rung nhẹ hoặc focus nếu người dùng chưa nhập gì
        input.focus();
        input.style.borderBottomColor = "red";
        setTimeout(() => input.style.borderBottomColor = "#ccc", 500);
    }
}

// === CHỨC NĂNG COMMENTS/REVIEWS ===
async function loadComments(placeId) {
    const reviewsContainer = document.getElementById('reviewsList');
    
    try {
        const response = await fetch(`${CONFIG.apiBase}/api/v1/comments/place/${placeId}`);
        
        if (!response.ok) {
            throw new Error('Failed to load comments');
        }
        
        const comments = await response.json();
        
        if (comments.length > 0) {
            reviewsContainer.innerHTML = comments.map(comment => {
                const date = new Date(comment.created_at).toLocaleDateString('vi-VN', {
                    year: 'numeric',
                    month: 'long',
                    day: 'numeric'
                });
                
                // Sử dụng display_name nếu có, không thì dùng username
                const displayName = comment.user_display_name || comment.username;
                
                // Sử dụng avatar_url nếu có, không thì dùng icon mặc định
                let avatarHtml;
                if (comment.user_avatar_url) {
                    // Nếu là relative URL, thêm backend URL
                    const fullAvatarUrl = comment.user_avatar_url.startsWith('http') 
                        ? comment.user_avatar_url 
                        : `${CONFIG.apiBase}${comment.user_avatar_url}`;
                    avatarHtml = `<img src="${fullAvatarUrl}" alt="${displayName}" style="width: 48px; height: 48px; border-radius: 50%; object-fit: cover;">`;
                } else {
                    avatarHtml = `<i class="fas fa-user-circle" style="font-size: 3rem; color: #14838B;"></i>`;
                }
                
                return `
                    <div class="review-card" data-comment-id="${comment.id}">
                        <div class="reviewer-avatar">
                            ${avatarHtml}
                        </div>
                        <div class="review-content">
                            <h4>${displayName}</h4>
                            <p style="font-size: 0.85rem; color: #999; margin: 5px 0;">${date}</p>
                            <p>${comment.content}</p>
                            <div style="margin-top: 10px;">
                                <button class="btn-like-comment" data-comment-id="${comment.id}" style="background: none; border: none; cursor: pointer; color: #999; font-size: 0.9rem; transition: all 0.3s;">
                                    <i class="far fa-heart"></i> <span class="like-text">Like</span>
                                </button>
                            </div>
                        </div>
                    </div>
                `;
            }).join('');
        } else {
            reviewsContainer.innerHTML = '<p style="text-align: center; color: #999; padding: 20px;">No reviews yet. Be the first to review!</p>';
        }
        
        // Setup like buttons for comments after loading
        await setupCommentLikeButtons();
    } catch (error) {
        console.error('Error loading comments:', error);
        reviewsContainer.innerHTML = '<p style="text-align: center; color: #999;">Failed to load reviews.</p>';
    }
}

// Toast notification helper
let toastTimeout;
let keyListener;

function showToast(message, type = 'success') {
    const toast = document.getElementById('toast');
    const toastMessage = document.getElementById('toastMessage');
    const icon = toast.querySelector('i');
    
    // Clear previous timeout and listener
    if (toastTimeout) clearTimeout(toastTimeout);
    if (keyListener) document.removeEventListener('keydown', keyListener);
    
    // Set message and icon
    toastMessage.textContent = message;
    
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
    
    // Show toast
    toast.classList.remove('hide');
    toast.classList.add('show');
    
    // Hide after 10s
    toastTimeout = setTimeout(() => {
        hideToast();
    }, 10000);
    
    // Close on any key press
    keyListener = (e) => {
        hideToast();
    };
    document.addEventListener('keydown', keyListener, { once: true });
}

function hideToast() {
    const toast = document.getElementById('toast');
    toast.classList.add('hide');
    
    setTimeout(() => {
        toast.classList.remove('show', 'hide');
    }, 400);
    
    if (toastTimeout) clearTimeout(toastTimeout);
    if (keyListener) document.removeEventListener('keydown', keyListener);
}

function setupCommentForm(placeId) {
    const submitBtn = document.querySelector('.submit-btn');
    const textarea = document.querySelector('.review-textarea');
    
    if (!submitBtn || !textarea) return;
    
    submitBtn.addEventListener('click', async () => {
        const content = textarea.value.trim();
        
        if (!content) {
            showToast('Please write something before posting!', 'warning');
            return;
        }
        
        const token = localStorage.getItem('token');
        
        if (!token) {
            showToast('You need to login to post a review!', 'warning');
            setTimeout(() => {
                localStorage.setItem('returnUrl', window.location.href);
                window.location.href = 'login.html';
            }, 2000);
            return;
        }
        
        try {
            const response = await fetch(`${CONFIG.apiBase}/api/v1/comments`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({
                    place_id: parseInt(placeId),
                    content: content
                })
            });
            
            if (response.status === 401) {
                showToast('Your session has expired. Please login again.', 'error');
                setTimeout(() => {
                    localStorage.clear();
                    localStorage.setItem('returnUrl', window.location.href);
                    window.location.href = 'login.html';
                }, 2000);
                return;
            }
            
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Failed to post comment');
            }
            
            // Clear textarea
            textarea.value = '';
            
            // Reload comments
            await loadComments(placeId);
            
            // Show success message
            showToast('✓ Review posted successfully!');
            
        } catch (error) {
            console.error('Error posting comment:', error);
            showToast(`Failed to post review: ${error.message}`, 'error');
        }
    });
}

// === LIKE/UNLIKE FUNCTIONALITY ===

// Setup place like/unlike buttons
function setupPlaceLikeButtons(placeId) {
    const btnLike = document.getElementById('btnLikePlace');
    const btnUnlike = document.getElementById('btnUnlikePlace');
    
    if (!btnLike || !btnUnlike) return;
    
    // Check if place is already liked
    checkPlaceLikeStatus(placeId);
    
    btnLike.addEventListener('click', async () => {
        await togglePlaceLike(placeId, true);
    });
    
    btnUnlike.addEventListener('click', async () => {
        await togglePlaceLike(placeId, false);
    });
}

// Check if current user has liked this place
async function checkPlaceLikeStatus(placeId) {
    const token = localStorage.getItem('token');
    if (!token) return;
    
    try {
        const response = await fetch(`${CONFIG.apiBase}/api/v1/likes/check/place/${placeId}`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (response.ok) {
            const data = await response.json();
            updatePlaceLikeUI(data.liked);
        }
    } catch (error) {
        console.error('Error checking place like status:', error);
    }
}

// Toggle place like/unlike
async function togglePlaceLike(placeId, isLike) {
    const token = localStorage.getItem('token');
    
    if (!token) {
        showToast('Please login to like places!', 'warning');
        setTimeout(() => {
            localStorage.setItem('returnUrl', window.location.href);
            window.location.href = 'login.html';
        }, 2000);
        return;
    }
    
    try {
        if (isLike) {
            // Like the place
            const response = await fetch(`${CONFIG.apiBase}/api/v1/likes/place`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({ place_id: parseInt(placeId) })
            });
            
            if (response.ok) {
                updatePlaceLikeUI(true);
                showToast('✓ Place added to your favorites!');
            } else if (response.status === 400) {
                showToast('You already liked this place!', 'warning');
            }
        } else {
            // Unlike the place
            const response = await fetch(`${CONFIG.apiBase}/api/v1/likes/place/${placeId}`, {
                method: 'DELETE',
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });
            
            if (response.ok) {
                updatePlaceLikeUI(false);
                showToast('Place removed from favorites', 'warning');
            }
        }
    } catch (error) {
        console.error('Error toggling place like:', error);
        showToast('Failed to update like status', 'error');
    }
}

// Update place like button UI
function updatePlaceLikeUI(isLiked) {
    const btnLike = document.getElementById('btnLikePlace');
    const btnUnlike = document.getElementById('btnUnlikePlace');
    
    if (isLiked) {
        btnLike.innerHTML = '<i class="fas fa-thumbs-up"></i>';
        btnLike.style.color = '#14838B';
        btnUnlike.innerHTML = '<i class="far fa-thumbs-down"></i>';
        btnUnlike.style.color = '';
    } else {
        btnLike.innerHTML = '<i class="far fa-thumbs-up"></i>';
        btnLike.style.color = '';
    }
}

// Setup comment like buttons
async function setupCommentLikeButtons() {
    const token = localStorage.getItem('token');
    const likeButtons = document.querySelectorAll('.btn-like-comment');
    
    // Check like status for each comment if user is logged in
    if (token) {
        for (const btn of likeButtons) {
            const commentId = btn.dataset.commentId;
            await checkCommentLikeStatus(commentId, btn);
        }
    }
    
    // Add click handlers
    likeButtons.forEach(btn => {
        btn.addEventListener('click', async (e) => {
            e.preventDefault();
            const commentId = btn.dataset.commentId;
            await toggleCommentLike(commentId, btn);
        });
        
        // Hover effect
        btn.addEventListener('mouseenter', () => {
            btn.style.color = '#14838B';
        });
        btn.addEventListener('mouseleave', () => {
            if (!btn.classList.contains('liked')) {
                btn.style.color = '#999';
            } else {
                btn.style.color = '#14838B';  // Keep teal if liked
            }
        });
    });
}

// Check if comment is liked
async function checkCommentLikeStatus(commentId, btn) {
    const token = localStorage.getItem('token');
    if (!token) return;
    
    try {
        const response = await fetch(`${CONFIG.apiBase}/api/v1/likes/check/comment/${commentId}`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (response.ok) {
            const data = await response.json();
            updateCommentLikeUI(btn, data.liked);
        }
    } catch (error) {
        console.error('Error checking comment like status:', error);
    }
}

// Toggle comment like
async function toggleCommentLike(commentId, btn) {
    const token = localStorage.getItem('token');
    
    if (!token) {
        showToast('Please login to like reviews!', 'warning');
        setTimeout(() => {
            localStorage.setItem('returnUrl', window.location.href);
            window.location.href = 'login.html';
        }, 2000);
        return;
    }
    
    const isLiked = btn.classList.contains('liked');
    
    try {
        if (isLiked) {
            // Unlike
            const response = await fetch(`${CONFIG.apiBase}/api/v1/likes/comment/${commentId}`, {
                method: 'DELETE',
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });
            
            if (response.ok) {
                updateCommentLikeUI(btn, false);
                showToast('Review unliked');
            }
        } else {
            // Like
            const response = await fetch(`${CONFIG.apiBase}/api/v1/likes/comment`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({ comment_id: parseInt(commentId) })
            });
            
            if (response.ok) {
                updateCommentLikeUI(btn, true);
                showToast('✓ Review liked!');
            } else if (response.status === 400) {
                showToast('You already liked this review!', 'warning');
            }
        }
    } catch (error) {
        console.error('Error toggling comment like:', error);
        showToast('Failed to update like status', 'error');
    }
}

// Update comment like button UI
function updateCommentLikeUI(btn, isLiked) {
    const icon = btn.querySelector('i');
    const text = btn.querySelector('.like-text');
    
    if (isLiked) {
        icon.className = 'fas fa-heart';
        text.textContent = 'Liked';
        btn.style.color = '#14838B';  // Teal color
        btn.classList.add('liked');
    } else {
        icon.className = 'far fa-heart';
        text.textContent = 'Like';
        btn.style.color = '#999';
        btn.classList.remove('liked');
    }
}