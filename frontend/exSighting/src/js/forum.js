/**
 * Forum Page JavaScript
 * Handles posts, likes, comments functionality
 */

import { API_BASE_URL } from './config.js';

// API base cho forum endpoints
const FORUM_API = `${API_BASE_URL}/api/v1/forum`;

// =========================================
// STATE MANAGEMENT
// =========================================
let currentUser = null;
let posts = [];
let currentFilter = 'all';
let selectedPlace = null;
let selectedImages = [];
let currentPage = 0;
const POSTS_PER_PAGE = 10;
let isLoading = false;
let hasMorePosts = true;

// =========================================
// DOM ELEMENTS
// =========================================
const postsFeed = document.getElementById('postsFeed');
const createPostSection = document.getElementById('createPostSection');
const loginPrompt = document.getElementById('loginPrompt');
const postContent = document.getElementById('postContent');
const submitPostBtn = document.getElementById('submitPostBtn');
const imagePreviewContainer = document.getElementById('imagePreviewContainer');
const postImagesInput = document.getElementById('postImages');
const selectPlaceBtn = document.getElementById('selectPlaceBtn');
const selectedPlaceName = document.getElementById('selectedPlaceName');
const selectedPlaceId = document.getElementById('selectedPlaceId');
const placeModal = document.getElementById('placeModal');
const closePlaceModal = document.getElementById('closePlaceModal');
const placeSearchInput = document.getElementById('placeSearchInput');
const placesList = document.getElementById('placesList');
const postDetailModal = document.getElementById('postDetailModal');
const closePostModal = document.getElementById('closePostModal');
const postDetailContent = document.getElementById('postDetailContent');
const loadingSpinner = document.getElementById('loadingSpinner');
const emptyState = document.getElementById('emptyState');
const loadMoreContainer = document.getElementById('loadMoreContainer');
const loadMoreBtn = document.getElementById('loadMoreBtn');
const currentUserAvatar = document.getElementById('currentUserAvatar');
const tabBtns = document.querySelectorAll('.tab-btn');

// =========================================
// INITIALIZATION
// =========================================
document.addEventListener('DOMContentLoaded', async () => {
    await checkAuth();
    await loadPosts();
    setupEventListeners();
});

// =========================================
// AUTHENTICATION
// =========================================
async function checkAuth() {
    const token = localStorage.getItem('token');
    console.log('🔑 Token from localStorage:', token ? 'exists' : 'missing');
    
    if (token) {
        try {
            const response = await fetch(`${API_BASE_URL}/api/v1/auth/profile`, {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });
            console.log('📡 API Response status:', response.status);
            
            if (response.ok) {
                currentUser = await response.json();
                console.log('✅ User data received:', currentUser);
                showCreatePostSection();
            } else {
                console.log('❌ API returned error:', response.status);
                showLoginPrompt();
            }
        } catch (error) {
            console.error('❌ Auth check failed:', error);
            showLoginPrompt();
        }
    } else {
        console.log('⚠️ No token found, showing login prompt');
        showLoginPrompt();
    }
}

function showCreatePostSection() {
    createPostSection.style.display = 'block';
    loginPrompt.style.display = 'none';
    
    // Update avatar
    if (currentUser && currentUser.avatar_url) {
        const avatarPath = currentUser.avatar_url.startsWith('/') 
            ? currentUser.avatar_url.substring(1) 
            : currentUser.avatar_url;
        currentUserAvatar.src = currentUser.avatar_url.startsWith('http') 
            ? currentUser.avatar_url 
            : `${API_BASE_URL}/${avatarPath}`;
    }
}

function showLoginPrompt() {
    createPostSection.style.display = 'none';
    loginPrompt.style.display = 'flex';
}

// =========================================
// LOAD POSTS
// =========================================
async function loadPosts(append = false) {
    if (isLoading) return;
    isLoading = true;
    
    if (!append) {
        loadingSpinner.style.display = 'flex';
        postsFeed.innerHTML = '';
        postsFeed.appendChild(loadingSpinner);
        currentPage = 0;
    }
    
    try {
        const skip = currentPage * POSTS_PER_PAGE;
        const headers = {};
        const token = localStorage.getItem('token');
        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }
        
        console.log('🔐 Fetching posts with headers:', headers);
        
        const response = await fetch(`${FORUM_API}/feed?skip=${skip}&limit=${POSTS_PER_PAGE}`, { headers });
        
        if (response.ok) {
            const newPosts = await response.json();
            console.log('Loaded posts:', newPosts.length, 'First post:', newPosts[0]);
            
            if (newPosts.length < POSTS_PER_PAGE) {
                hasMorePosts = false;
                loadMoreContainer.style.display = 'none';
            } else {
                hasMorePosts = true;
                loadMoreContainer.style.display = 'block';
            }
            
            if (append) {
                posts = [...posts, ...newPosts];
            } else {
                posts = newPosts;
            }
            
            renderPosts(newPosts, append);
            currentPage++;
            
        } else {
            console.error('Failed to load posts');
            showEmptyState();
        }
    } catch (error) {
        console.error('Error loading posts:', error);
        showEmptyState();
    } finally {
        isLoading = false;
        loadingSpinner.style.display = 'none';
    }
}

function renderPosts(postsToRender, append = false) {
    if (!append) {
        postsFeed.innerHTML = '';
    }
    
    if (posts.length === 0) {
        showEmptyState();
        return;
    }
    
    emptyState.style.display = 'none';
    
    // Filter posts based on current filter
    let filteredPosts = postsToRender;
    if (currentFilter === 'popular') {
        filteredPosts = [...postsToRender].sort((a, b) => (b.likes_count || 0) - (a.likes_count || 0));
    } else if (currentFilter === 'recent') {
        filteredPosts = [...postsToRender].sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
    }
    
    filteredPosts.forEach(post => {
        const postCard = createPostCard(post);
        postsFeed.appendChild(postCard);
    });
}

function createPostCard(post) {
    const card = document.createElement('div');
    card.className = 'post-card';
    card.dataset.postId = post.id;
    
    // Format date - ensure UTC is properly handled
    let postDateStr = post.created_at;
    if (typeof postDateStr === 'string' && !postDateStr.endsWith('Z') && !postDateStr.includes('+')) {
        postDateStr = postDateStr + 'Z';
    }
    const postDate = new Date(postDateStr);
    const timeAgo = getTimeAgo(postDate);
    
    // Parse images
    let images = [];
    try {
        // Backend trả về images dưới dạng array hoặc JSON string
        if (Array.isArray(post.images)) {
            images = post.images;
        } else if (typeof post.images === 'string') {
            images = JSON.parse(post.images);
        }
    } catch (e) {
        console.error('Error parsing images:', e);
        images = [];
    }
    
    // Check if current user liked this post
    const isLiked = post.is_liked || false;
    
    // Debug log
    if (currentUser) {
        console.log(`Post ${post.id}: is_liked=${post.is_liked}, like_count=${post.like_count}`);
    }
    
    card.innerHTML = `
        <div class="post-header">
            <img src="${getAvatarUrl(post.user)}" alt="Avatar" class="post-avatar">
            <div class="post-user-info">
                <span class="post-username">${post.user?.display_name || post.user?.username || 'Anonymous'}</span>
                <span class="post-time">${timeAgo}</span>
            </div>
            ${currentUser && currentUser.id === post.user_id ? `
                <button class="post-menu-btn" onclick="showPostMenu(${post.id})">
                    <i class="fas fa-ellipsis-h"></i>
                </button>
            ` : ''}
        </div>
        
        ${post.place ? `
            <a href="detail.html?id=${post.place_id}" class="post-place-tag">
                <i class="fas fa-map-marker-alt"></i> ${post.place.name}
            </a>
        ` : ''}
        
        <div class="post-content">
            <p>${formatContent(post.content)}</p>
        </div>
        
        ${images.length > 0 ? `
            <div class="post-images ${images.length === 1 ? 'single' : images.length === 2 ? 'double' : 'grid'}">
                ${images.slice(0, 4).map((img, idx) => {
                    const imgUrl = getImageUrl(img);
                    return `
                    <div class="post-image-container ${idx === 3 && images.length > 4 ? 'more-overlay' : ''}">
                        <img src="${imgUrl}" alt="Post image" onclick="viewImage('${imgUrl}')">
                        ${idx === 3 && images.length > 4 ? `<span class="more-count">+${images.length - 4}</span>` : ''}
                    </div>
                    `;
                }).join('')}
            </div>
        ` : ''}
        
        <div class="post-stats">
            <span class="likes-count">
                <i class="fas fa-heart"></i> ${post.like_count || 0} likes
            </span>
            <span class="comments-count" onclick="openPostDetail(${post.id})">
                ${post.comment_count || 0} comments
            </span>
        </div>
        
        <div class="post-actions">
            <button class="action-btn like-btn ${isLiked ? 'liked' : ''}" onclick="toggleLike(${post.id})">
                <i class="${isLiked ? 'fas' : 'far'} fa-heart"></i>
                <span>Like</span>
            </button>
            <button class="action-btn comment-btn" onclick="openPostDetail(${post.id})">
                <i class="far fa-comment"></i>
                <span>Comment</span>
            </button>
            <button class="action-btn share-btn" onclick="sharePost(${post.id})">
                <i class="far fa-share-square"></i>
                <span>Share</span>
            </button>
        </div>
    `;
    
    return card;
}

function getAvatarUrl(user) {
    if (!user || !user.avatar_url) {
        return 'src/images/default-avatar.png';
    }
    if (user.avatar_url.startsWith('http')) {
        return user.avatar_url;
    }
    const avatarPath = user.avatar_url.startsWith('/') ? user.avatar_url.substring(1) : user.avatar_url;
    return `${API_BASE_URL}/${avatarPath}`;
}

function getImageUrl(imagePath) {
    if (!imagePath) return '';
    if (imagePath.startsWith('http')) return imagePath;
    const path = imagePath.startsWith('/') ? imagePath.substring(1) : imagePath;
    return `${API_BASE_URL}/${path}`;
}

function getTimeAgo(date) {
    // Ensure date is a valid Date object
    if (!(date instanceof Date)) {
        date = new Date(date);
    }
    
    // Calculate seconds difference
    const seconds = Math.floor((Date.now() - date.getTime()) / 1000);
    
    // Handle future dates (clock skew)
    if (seconds < 0) {
        return 'Just now';
    }
    
    const intervals = {
        year: 31536000,
        month: 2592000,
        week: 604800,
        day: 86400,
        hour: 3600,
        minute: 60
    };
    
    for (const [unit, secondsInUnit] of Object.entries(intervals)) {
        const interval = Math.floor(seconds / secondsInUnit);
        if (interval >= 1) {
            return `${interval} ${unit}${interval > 1 ? 's' : ''} ago`;
        }
    }
    
    return 'Just now';
}

function formatContent(content) {
    // Convert URLs to links
    const urlRegex = /(https?:\/\/[^\s]+)/g;
    let formatted = content.replace(urlRegex, '<a href="$1" target="_blank" rel="noopener">$1</a>');
    
    // Convert hashtags
    const hashtagRegex = /#(\w+)/g;
    formatted = formatted.replace(hashtagRegex, '<span class="hashtag">#$1</span>');
    
    // Convert newlines to br
    formatted = formatted.replace(/\n/g, '<br>');
    
    return formatted;
}

function showEmptyState() {
    emptyState.style.display = 'flex';
    loadMoreContainer.style.display = 'none';
}

// =========================================
// CREATE POST
// =========================================
async function createPost() {
    const content = postContent.value.trim();
    
    if (!content && selectedImages.length === 0) {
        showToast('Please write something or add photos', 'error');
        return;
    }
    
    if (!currentUser) {
        showToast('Please sign in to post', 'error');
        return;
    }
    
    submitPostBtn.disabled = true;
    submitPostBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Posting...';
    
    try {
        // Upload images first if any
        let imageUrls = [];
        if (selectedImages.length > 0) {
            imageUrls = await uploadImages(selectedImages);
        }
        
        const postData = {
            content: content,
            images: imageUrls,
            place_id: selectedPlace ? selectedPlace.id : null
        };
        
        const response = await fetch(`${FORUM_API}/posts`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${localStorage.getItem('token')}`
            },
            body: JSON.stringify(postData)
        });
        
        if (response.ok) {
            const newPost = await response.json();
            console.log('✅ New post created:', newPost);
            console.log('📸 Images in new post:', newPost.images);
            showToast('Post created successfully!', 'success');
            
            // Reset form
            postContent.value = '';
            selectedImages = [];
            imagePreviewContainer.innerHTML = '';
            selectedPlace = null;
            selectedPlaceName.textContent = '';
            selectedPlaceId.value = '';
            
            // Add new post to feed
            posts.unshift(newPost);
            const postCard = createPostCard(newPost);
            postsFeed.insertBefore(postCard, postsFeed.firstChild);
            emptyState.style.display = 'none';
            
        } else {
            const error = await response.json();
            showToast(error.detail || 'Failed to create post', 'error');
        }
    } catch (error) {
        console.error('Error creating post:', error);
        showToast('Failed to create post. Please try again.', 'error');
    } finally {
        submitPostBtn.disabled = false;
        submitPostBtn.innerHTML = '<i class="fas fa-paper-plane"></i> Post';
    }
}

async function uploadImages(images) {
    const formData = new FormData();
    images.forEach((img, idx) => {
        formData.append('files', img);
    });
    
    try {
        const response = await fetch(`${FORUM_API}/upload`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('token')}`
            },
            body: formData
        });
        
        if (response.ok) {
            const result = await response.json();
            return result.urls || [];
        }
    } catch (error) {
        console.error('Error uploading images:', error);
    }
    
    return [];
}

function handleImageSelect(event) {
    const files = Array.from(event.target.files);
    
    if (files.length + selectedImages.length > 10) {
        showToast('Maximum 10 images allowed', 'error');
        return;
    }
    
    files.forEach(file => {
        if (file.type.startsWith('image/')) {
            selectedImages.push(file);
            addImagePreview(file);
        }
    });
    
    event.target.value = '';
}

function addImagePreview(file) {
    const reader = new FileReader();
    reader.onload = (e) => {
        const preview = document.createElement('div');
        preview.className = 'image-preview';
        preview.innerHTML = `
            <img src="${e.target.result}" alt="Preview">
            <button class="remove-btn" onclick="removeImage(this, '${file.name}')">
                <i class="fas fa-times"></i>
            </button>
        `;
        imagePreviewContainer.appendChild(preview);
    };
    reader.readAsDataURL(file);
}

// Global function for removing images
window.removeImage = function(btn, fileName) {
    const index = selectedImages.findIndex(f => f.name === fileName);
    if (index > -1) {
        selectedImages.splice(index, 1);
    }
    btn.parentElement.remove();
};

// =========================================
// LIKE FUNCTIONALITY
// =========================================
window.toggleLike = async function(postId) {
    if (!currentUser) {
        showToast('Please sign in to like posts', 'error');
        return;
    }
    
    // Find post card using dataset selector
    const postCard = Array.from(document.querySelectorAll('.post-card')).find(
        card => card.dataset.postId == postId
    );
    
    if (!postCard) {
        console.error('Post card not found for id:', postId);
        return;
    }
    
    const likeBtn = postCard.querySelector('.like-btn');
    const heartIcon = likeBtn.querySelector('i');
    const likesCount = postCard.querySelector('.likes-count');
    
    try {
        const response = await fetch(`${FORUM_API}/posts/${postId}/like`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('token')}`
            }
        });
        
        if (response.ok) {
            const result = await response.json();
            
            // Backend returns: {action: "liked" or "unliked", like_count: number}
            const isLiked = result.action === 'liked';
            
            if (isLiked) {
                likeBtn.classList.add('liked');
                heartIcon.classList.remove('far');
                heartIcon.classList.add('fas');
            } else {
                likeBtn.classList.remove('liked');
                heartIcon.classList.remove('fas');
                heartIcon.classList.add('far');
            }
            
            // Update count
            likesCount.innerHTML = `<i class="fas fa-heart"></i> ${result.like_count} likes`;
            
            // Update in posts array
            const postIndex = posts.findIndex(p => p.id === postId);
            if (postIndex > -1) {
                posts[postIndex].like_count = result.like_count;
                posts[postIndex].is_liked = isLiked;
            }
        }
    } catch (error) {
        console.error('Error toggling like:', error);
        showToast('Failed to like post', 'error');
    }
};

// Toggle like trong modal
window.toggleLikeInModal = async function(postId) {
    if (!currentUser) {
        showToast('Please sign in to like posts', 'error');
        return;
    }
    
    const modal = document.querySelector('.post-detail');
    if (!modal) return;
    
    const likeBtn = modal.querySelector('.like-btn');
    const heartIcon = likeBtn.querySelector('i');
    const likesCount = document.getElementById(`likesCountModal-${postId}`);
    
    try {
        const response = await fetch(`${FORUM_API}/posts/${postId}/like`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('token')}`
            }
        });
        
        if (response.ok) {
            const result = await response.json();
            const isLiked = result.action === 'liked';
            
            // Update button state
            if (isLiked) {
                likeBtn.classList.add('liked');
                heartIcon.classList.remove('far');
                heartIcon.classList.add('fas');
            } else {
                likeBtn.classList.remove('liked');
                heartIcon.classList.remove('fas');
                heartIcon.classList.add('far');
            }
            
            // Update count in modal
            likesCount.innerHTML = `<i class="fas fa-heart"></i> ${result.like_count} likes`;
            
            // Update in main feed if post card exists
            const postCard = Array.from(document.querySelectorAll('.post-card')).find(
                card => card.dataset.postId == postId
            );
            if (postCard) {
                const feedLikeBtn = postCard.querySelector('.like-btn');
                const feedHeartIcon = feedLikeBtn.querySelector('i');
                const feedLikesCount = postCard.querySelector('.likes-count');
                
                if (isLiked) {
                    feedLikeBtn.classList.add('liked');
                    feedHeartIcon.classList.remove('far');
                    feedHeartIcon.classList.add('fas');
                } else {
                    feedLikeBtn.classList.remove('liked');
                    feedHeartIcon.classList.remove('fas');
                    feedHeartIcon.classList.add('far');
                }
                feedLikesCount.innerHTML = `<i class="fas fa-heart"></i> ${result.like_count} likes`;
            }
            
            // Update in posts array
            const postIndex = posts.findIndex(p => p.id === postId);
            if (postIndex > -1) {
                posts[postIndex].like_count = result.like_count;
                posts[postIndex].is_liked = isLiked;
            }
        }
    } catch (error) {
        console.error('Error toggling like in modal:', error);
        showToast('Failed to like post', 'error');
    }
};

// =========================================
// COMMENTS & POST DETAIL
// =========================================
window.openPostDetail = async function(postId) {
    postDetailModal.classList.add('active');
    postDetailContent.innerHTML = '<div class="loading-spinner"><i class="fas fa-spinner fa-spin"></i></div>';
    
    try {
        const headers = {};
        const token = localStorage.getItem('token');
        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }
        
        const response = await fetch(`${FORUM_API}/posts/${postId}`, { headers });
        
        if (response.ok) {
            const post = await response.json();
            renderPostDetail(post);
        } else {
            postDetailContent.innerHTML = '<p class="error-msg">Failed to load post</p>';
        }
    } catch (error) {
        console.error('Error loading post detail:', error);
        postDetailContent.innerHTML = '<p class="error-msg">Failed to load post</p>';
    }
};

function renderPostDetail(post) {
    // Parse images
    let images = [];
    try {
        if (Array.isArray(post.images)) {
            images = post.images;
        } else if (typeof post.images === 'string') {
            images = JSON.parse(post.images);
        }
    } catch (e) {
        console.error('Error parsing images:', e);
        images = [];
    }
    
    let postDateStr = post.created_at;
    if (typeof postDateStr === 'string' && !postDateStr.endsWith('Z') && !postDateStr.includes('+')) {
        postDateStr = postDateStr + 'Z';
    }
    const postDate = new Date(postDateStr);
    
    postDetailContent.innerHTML = `
        <div class="post-detail">
            <div class="post-header">
                <img src="${getAvatarUrl(post.user)}" alt="Avatar" class="post-avatar">
                <div class="post-user-info">
                    <span class="post-username">${post.user?.display_name || post.user?.username || 'Anonymous'}</span>
                    <span class="post-time">${getTimeAgo(postDate)}</span>
                </div>
            </div>
            
            ${post.place ? `
                <a href="detail.html?id=${post.place_id}" class="post-place-tag">
                    <i class="fas fa-map-marker-alt"></i> ${post.place.name}
                </a>
            ` : ''}
            
            <div class="post-content">
                <p>${formatContent(post.content)}</p>
            </div>
            
            ${images.length > 0 ? `
                <div class="post-images-gallery">
                    ${images.map(img => {
                        const imgUrl = getImageUrl(img);
                        return `<img src="${imgUrl}" alt="Post image" onclick="viewImage('${imgUrl}')">`;
                    }).join('')}
                </div>
            ` : ''}
            
            <div class="post-stats">
                <span class="likes-count-modal" id="likesCountModal-${post.id}">
                    <i class="fas fa-heart"></i> ${post.like_count || 0} likes
                </span>
                <span><i class="fas fa-comment"></i> ${post.comments?.length || 0} comments</span>
            </div>
            
            ${currentUser ? `
                <div class="post-actions">
                    <button class="action-btn like-btn ${post.is_liked ? 'liked' : ''}" onclick="toggleLikeInModal(${post.id})">
                        <i class="${post.is_liked ? 'fas' : 'far'} fa-heart"></i>
                        <span>Like</span>
                    </button>
                    <button class="action-btn comment-btn" onclick="document.getElementById('commentInput-${post.id}').focus()">
                        <i class="far fa-comment"></i>
                        <span>Comment</span>
                    </button>
                </div>
            ` : ''}
            
            <div class="comments-section">
                <h4>Comments</h4>
                <div class="comments-list" id="commentsList-${post.id}">
                    ${post.comments && post.comments.length > 0 ? 
                        post.comments.map(comment => createCommentHTML(comment)).join('') :
                        '<p class="no-comments">No comments yet. Be the first to comment!</p>'
                    }
                </div>
                
                ${currentUser ? `
                    <div class="add-comment">
                        <img src="${getAvatarUrl(currentUser)}" alt="Avatar" class="comment-avatar">
                        <input type="text" id="commentInput-${post.id}" placeholder="Write a comment...">
                        <button onclick="submitComment(${post.id})">
                            <i class="fas fa-paper-plane"></i>
                        </button>
                    </div>
                ` : `
                    <p class="login-to-comment">
                        <a href="login.html">Sign in</a> to leave a comment
                    </p>
                `}
            </div>
        </div>
    `;
}

function createCommentHTML(comment) {
    let commentDateStr = comment.created_at;
    if (typeof commentDateStr === 'string' && !commentDateStr.endsWith('Z') && !commentDateStr.includes('+')) {
        commentDateStr = commentDateStr + 'Z';
    }
    const commentDate = new Date(commentDateStr);
    return `
        <div class="comment-item" data-comment-id="${comment.id}">
            <img src="${getAvatarUrl(comment.user)}" alt="Avatar" class="comment-avatar">
            <div class="comment-body">
                <span class="comment-username">${comment.user?.display_name || comment.user?.username || 'Anonymous'}</span>
                <p class="comment-text">${formatContent(comment.content)}</p>
                <span class="comment-time">${getTimeAgo(commentDate)}</span>
            </div>
            ${currentUser && currentUser.id === comment.user_id ? `
                <button class="delete-comment-btn" onclick="deleteComment(${comment.post_id}, ${comment.id})">
                    <i class="fas fa-trash"></i>
                </button>
            ` : ''}
        </div>
    `;
}

window.submitComment = async function(postId) {
    const input = document.getElementById(`commentInput-${postId}`);
    const content = input.value.trim();
    
    if (!content) return;
    
    try {
        const response = await fetch(`${FORUM_API}/posts/${postId}/comments`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${localStorage.getItem('token')}`
            },
            body: JSON.stringify({ content })
        });
        
        if (response.ok) {
            const newComment = await response.json();
            
            // Add comment to list
            const commentsList = document.getElementById(`commentsList-${postId}`);
            const noComments = commentsList.querySelector('.no-comments');
            if (noComments) noComments.remove();
            
            commentsList.insertAdjacentHTML('beforeend', createCommentHTML(newComment));
            input.value = '';
            
            // Update comment count in feed
            const postCard = document.querySelector(`.post-card[data-post-id="${postId}"]`);
            if (postCard) {
                const commentsCount = postCard.querySelector('.comments-count');
                const currentCount = parseInt(commentsCount.textContent) || 0;
                commentsCount.textContent = `${currentCount + 1} comments`;
            }
            
            showToast('Comment added!', 'success');
        }
    } catch (error) {
        console.error('Error adding comment:', error);
        showToast('Failed to add comment', 'error');
    }
};

window.deleteComment = async function(postId, commentId) {
    if (!confirm('Delete this comment?')) return;
    
    try {
        const response = await fetch(`${FORUM_API}/posts/${postId}/comments/${commentId}`, {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('token')}`
            }
        });
        
        if (response.ok) {
            document.querySelector(`.comment-item[data-comment-id="${commentId}"]`).remove();
            showToast('Comment deleted', 'success');
        }
    } catch (error) {
        console.error('Error deleting comment:', error);
        showToast('Failed to delete comment', 'error');
    }
};

// =========================================
// PLACE SELECTION
// =========================================
async function loadPlaces(query = '') {
    try {
        const url = query 
            ? `${API_BASE_URL}/api/v1/place/search/by-name?name=${encodeURIComponent(query)}&limit=20`
            : `${API_BASE_URL}/api/v1/place/search/by-name?name=&limit=20`;
        
        const response = await fetch(url);
        
        if (response.ok) {
            const places = await response.json();
            renderPlacesList(places);
        }
    } catch (error) {
        console.error('Error loading places:', error);
    }
}

function renderPlacesList(places) {
    placesList.innerHTML = places.map(place => `
        <div class="place-item" onclick="selectPlace(${place.id}, '${place.name.replace(/'/g, "\\'")}')">
            <img src="${place.images?.[0] || 'src/images/placeholder.jpg'}" alt="${place.name}">
            <div class="place-info">
                <span class="place-name">${place.name}</span>
                <span class="place-location">${place.province || ''}</span>
            </div>
        </div>
    `).join('');
}

window.selectPlace = function(id, name) {
    selectedPlace = { id, name };
    selectedPlaceName.textContent = name;
    selectedPlaceId.value = id;
    placeModal.classList.remove('active');
};

// =========================================
// POST MENU & DELETE
// =========================================
window.showPostMenu = function(postId) {
    if (confirm('Do you want to delete this post?')) {
        deletePost(postId);
    }
};

async function deletePost(postId) {
    try {
        const response = await fetch(`${FORUM_API}/posts/${postId}`, {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('token')}`
            }
        });
        
        if (response.ok) {
            // Remove from DOM
            const postCard = document.querySelector(`.post-card[data-post-id="${postId}"]`);
            if (postCard) {
                postCard.remove();
            }
            
            // Remove from posts array
            posts = posts.filter(p => p.id !== postId);
            
            if (posts.length === 0) {
                showEmptyState();
            }
            
            showToast('Post deleted', 'success');
        } else {
            showToast('Failed to delete post', 'error');
        }
    } catch (error) {
        console.error('Error deleting post:', error);
        showToast('Failed to delete post', 'error');
    }
}

// =========================================
// SHARE & IMAGE VIEWER
// =========================================
window.sharePost = function(postId) {
    const url = `${window.location.origin}/forum.html?post=${postId}`;
    
    if (navigator.share) {
        navigator.share({
            title: 'Check out this post on exSighting',
            url: url
        });
    } else {
        navigator.clipboard.writeText(url).then(() => {
            showToast('Link copied to clipboard!', 'success');
        });
    }
};

window.viewImage = function(imageUrl) {
    // Create lightbox
    const lightbox = document.createElement('div');
    lightbox.className = 'image-lightbox';
    lightbox.innerHTML = `
        <div class="lightbox-overlay" onclick="closeLightbox()"></div>
        <img src="${imageUrl}" alt="Full size image">
        <button class="close-lightbox" onclick="closeLightbox()">
            <i class="fas fa-times"></i>
        </button>
    `;
    document.body.appendChild(lightbox);
    document.body.style.overflow = 'hidden';
};

window.closeLightbox = function() {
    const lightbox = document.querySelector('.image-lightbox');
    if (lightbox) {
        lightbox.remove();
        document.body.style.overflow = '';
    }
};

// =========================================
// EVENT LISTENERS
// =========================================
function setupEventListeners() {
    // Submit post
    submitPostBtn?.addEventListener('click', createPost);
    
    // Image selection
    postImagesInput?.addEventListener('change', handleImageSelect);
    
    // Place selection modal
    selectPlaceBtn?.addEventListener('click', () => {
        placeModal.classList.add('active');
        loadPlaces();
    });
    
    closePlaceModal?.addEventListener('click', () => {
        placeModal.classList.remove('active');
    });
    
    // Place search
    let searchTimeout;
    placeSearchInput?.addEventListener('input', (e) => {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(() => {
            loadPlaces(e.target.value);
        }, 300);
    });
    
    // Close post detail modal
    closePostModal?.addEventListener('click', () => {
        postDetailModal.classList.remove('active');
    });
    
    // Tab filters
    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            tabBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            currentFilter = btn.dataset.filter;
            renderPosts(posts);
        });
    });
    
    // Load more
    loadMoreBtn?.addEventListener('click', () => {
        loadPosts(true);
    });
    
    // Close modals on outside click
    placeModal?.addEventListener('click', (e) => {
        if (e.target === placeModal) {
            placeModal.classList.remove('active');
        }
    });
    
    postDetailModal?.addEventListener('click', (e) => {
        if (e.target === postDetailModal) {
            postDetailModal.classList.remove('active');
        }
    });
    
    // Enter key for comment
    document.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && e.target.id.startsWith('commentInput-')) {
            const postId = e.target.id.replace('commentInput-', '');
            window.submitComment(parseInt(postId));
        }
    });
    
    // Check for post parameter in URL
    const urlParams = new URLSearchParams(window.location.search);
    const postId = urlParams.get('post');
    if (postId) {
        setTimeout(() => window.openPostDetail(parseInt(postId)), 500);
    }
}

// =========================================
// TOAST NOTIFICATIONS
// =========================================
function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.innerHTML = `
        <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-circle' : 'info-circle'}"></i>
        <span>${message}</span>
    `;
    
    document.body.appendChild(toast);
    
    setTimeout(() => toast.classList.add('show'), 10);
    
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}
