import { CONFIG } from './config.js';

document.addEventListener('DOMContentLoaded', async () => {
    try {
        checkAuth();
        loadProfileData();
        initTabs();
        initEditProfile();
        // Don't load reviews on page load, only when tab is clicked
    } catch (error) {
        console.error('Error initializing profile page:', error);
    }
});

function checkAuth() {
    const token = localStorage.getItem('token');
    const username = localStorage.getItem('username');
    
    const unsigned = document.getElementById('unsignedBlock');
    const signed = document.getElementById('signedBlock');
    const displayUser = document.getElementById('displayUsername');

    if (token && username) {
        if(unsigned) unsigned.style.display = 'none';
        if(signed) signed.style.display = 'inline-block';
        if(displayUser) displayUser.textContent = username;
    } else {
        // Nếu chưa login, chuyển về trang login
        window.location.href = 'login.html';
        return;
    }

    // Logout
    const btnLogout = document.getElementById('btnLogout');
    if (btnLogout) {
        btnLogout.addEventListener('click', (e) => {
            e.preventDefault();
            localStorage.clear();
            window.location.href = 'login.html';
        });
    }
}

async function loadProfileData() {
    try {
        const token = localStorage.getItem('token');
        if (!token) {
            window.location.href = 'login.html';
            return;
        }

        // Fetch user profile từ backend
        const response = await fetch(`${CONFIG.apiBase}/api/v1/auth/profile`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });

        if (!response.ok) {
            throw new Error('Failed to load profile');
        }

        const userData = await response.json();
        console.log('Loaded user data:', userData);

        // Lưu vào localStorage để dùng cho các trang khác
        localStorage.setItem('username', userData.username);
        if (userData.display_name) {
            localStorage.setItem('displayName', userData.display_name);
        }
        if (userData.avatar_url) {
            localStorage.setItem('avatarUrl', userData.avatar_url);
        }
        if (userData.bio) {
            localStorage.setItem('bio', userData.bio);
        }
        if (userData.location) {
            localStorage.setItem('location', userData.location);
        }

        const displayName = userData.display_name || userData.username || 'User';
        const username = userData.username || 'user';
        const avatarUrl = userData.avatar_url;
        
        // Update profile display
        document.getElementById('profileName').textContent = displayName;
        document.getElementById('profileUsername').textContent = `@${username.toLowerCase()}`;
        
        // Update avatar
        const profileAvatar = document.getElementById('profileAvatar');
        const headerAvatar = document.getElementById('headerAvatar');
        if (avatarUrl) {
            // Nếu là relative URL, thêm backend URL
            const fullAvatarUrl = avatarUrl.startsWith('http') ? avatarUrl : `${CONFIG.apiBase}${avatarUrl}`;
            profileAvatar.innerHTML = `<img src="${fullAvatarUrl}" alt="Avatar" style="width: 100%; height: 100%; border-radius: 50%; object-fit: cover;">`;
            headerAvatar.innerHTML = `<img src="${fullAvatarUrl}" alt="Avatar" style="width: 100%; height: 100%; border-radius: 50%; object-fit: cover;">`;
        } else {
            // Default avatar icon
            profileAvatar.innerHTML = `<i class="fas fa-user-circle"></i>`;
            headerAvatar.innerHTML = `<i class="fas fa-user-circle"></i>`;
        }
        
        // Update info section
        document.getElementById('infoName').textContent = displayName;
        document.getElementById('infoEmail').textContent = `${username}@example.com`; // Email placeholder
        
        // Update location nếu có
        const infoLocation = document.getElementById('infoLocation');
        if (userData.location) {
            infoLocation.textContent = userData.location;
            infoLocation.parentElement.style.display = 'flex';
        } else {
            infoLocation.parentElement.style.display = 'none';
        }
        
        // Simulated join date
        const joinDate = new Date(2024, 0, 1);
        document.getElementById('infoJoined').textContent = joinDate.toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        });
    } catch (error) {
        console.error('Error loading profile data:', error);
        alert('Failed to load profile data');
    }
}

function initTabs() {
    const tabBtns = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');
    
    // Sidebar navigation
    const sidebarItems = document.querySelectorAll('.sidebar-item[data-tab]');
    sidebarItems.forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            const targetTab = item.dataset.tab;
            
            // Find and click the corresponding tab button
            const tabBtn = document.querySelector(`.tab-btn[data-tab="${targetTab}"]`);
            if (tabBtn) tabBtn.click();
        });
    });
    
    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const targetTab = btn.dataset.tab;
            
            // Remove active class from all
            tabBtns.forEach(b => b.classList.remove('active'));
            tabContents.forEach(c => c.classList.remove('active'));
            
            // Add active to clicked
            btn.classList.add('active');
            const tabContent = document.getElementById(`${targetTab}-tab`);
            if (tabContent) {
                tabContent.classList.add('active');
            }
            
            // Load reviews when Reviews tab is clicked
            if (targetTab === 'reviews') {
                loadReviews();
            }
            
            // Load liked content when Liked tab is clicked
            if (targetTab === 'liked') {
                initLikedSubtabs();
                loadLikedComments(); // Load comments by default
            }
        });
    });
}

function initEditProfile() {
    const modal = document.getElementById('editProfileModal');
    const btnEdit = document.getElementById('btnEditProfile');
    const btnClose = document.getElementById('closeEditModal');
    const btnCancel = document.getElementById('btnCancelEdit');
    const form = document.getElementById('editProfileForm');
    const avatarInput = document.getElementById('editAvatar');
    const avatarPreview = document.getElementById('avatarPreview');
    const previewImg = document.getElementById('previewImg');
    
    // Preview avatar khi chọn file
    avatarInput.addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (file) {
            // Kiểm tra file size
            if (file.size > 5 * 1024 * 1024) {
                alert('File size too large. Maximum 5MB');
                avatarInput.value = '';
                avatarPreview.style.display = 'none';
                return;
            }
            
            // Hiển thị preview
            const reader = new FileReader();
            reader.onload = (e) => {
                previewImg.src = e.target.result;
                avatarPreview.style.display = 'block';
            };
            reader.readAsDataURL(file);
        } else {
            avatarPreview.style.display = 'none';
        }
    });
    
    // Open modal
    btnEdit.addEventListener('click', async () => {
        // Load current data từ backend
        const token = localStorage.getItem('token');
        if (!token) return;
        
        try {
            const response = await fetch(`${CONFIG.apiBase}/api/v1/auth/profile`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            
            if (response.ok) {
                const userData = await response.json();
                document.getElementById('editDisplayName').value = userData.display_name || userData.username || '';
                document.getElementById('editBio').value = userData.bio || '';
                document.getElementById('editLocation').value = userData.location || '';
                
                // Clear file input và preview
                avatarInput.value = '';
                avatarPreview.style.display = 'none';
            }
        } catch (error) {
            console.error('Error loading profile:', error);
        }
        
        modal.style.display = 'flex';
    });
    
    // Close modal
    const closeModal = () => {
        modal.style.display = 'none';
    };
    
    btnClose.addEventListener('click', closeModal);
    btnCancel.addEventListener('click', closeModal);
    
    // Click outside to close
    modal.addEventListener('click', (e) => {
        if (e.target === modal) closeModal();
    });
    
    // Submit form
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const displayName = document.getElementById('editDisplayName').value.trim();
        const bio = document.getElementById('editBio').value.trim();
        const location = document.getElementById('editLocation').value.trim();
        const avatarFile = avatarInput.files[0];
        
        const token = localStorage.getItem('token');
        if (!token) {
            alert('Please login first');
            window.location.href = 'login.html';
            return;
        }

        try {
            let avatarUrl = null;
            
            // Nếu có upload avatar, upload trước
            if (avatarFile) {
                const formData = new FormData();
                formData.append('file', avatarFile);
                
                const uploadResponse = await fetch(`${CONFIG.apiBase}/api/v1/auth/upload-avatar`, {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${token}`
                    },
                    body: formData
                });
                
                if (!uploadResponse.ok) {
                    throw new Error('Failed to upload avatar');
                }
                
                const uploadResult = await uploadResponse.json();
                avatarUrl = uploadResult.avatar_url;
                console.log('Avatar uploaded:', avatarUrl);
            }
            
            // Update profile với các fields khác
            const updateData = {
                display_name: displayName || null,
                bio: bio || null,
                location: location || null
            };
            
            // Nếu đã upload avatar, thêm vào update data
            if (avatarUrl) {
                updateData.avatar_url = avatarUrl;
            }
            
            const response = await fetch(`${CONFIG.apiBase}/api/v1/auth/profile`, {
                method: 'PUT',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(updateData)
            });

            if (!response.ok) {
                throw new Error('Failed to update profile');
            }

            const updatedUser = await response.json();
            console.log('Profile updated:', updatedUser);

            // Update localStorage
            if (updatedUser.display_name) {
                localStorage.setItem('displayName', updatedUser.display_name);
            }
            if (updatedUser.avatar_url) {
                localStorage.setItem('avatarUrl', updatedUser.avatar_url);
            }
            if (updatedUser.bio) {
                localStorage.setItem('bio', updatedUser.bio);
            }
            if (updatedUser.location) {
                localStorage.setItem('location', updatedUser.location);
            }

            // Close modal and reload profile
            closeModal();
            await loadProfileData();
            
            alert('Profile updated successfully!');
        } catch (error) {
            console.error('Error updating profile:', error);
            alert('Failed to update profile. Please try again.');
        }
    });
}

async function loadReviews() {
    const reviewsList = document.getElementById('reviewsList');
    const username = localStorage.getItem('username');
    const token = localStorage.getItem('token');
    
    console.log('Loading reviews...', { username, hasToken: !!token });
    
    if (!token || !username) {
        reviewsList.innerHTML = '<p style="text-align: center; color: #999; padding: 2rem;">Please login to view reviews</p>';
        return;
    }
    
    try {
        // Lấy tất cả comments của user
        const url = `${CONFIG.apiBase}/api/v1/comments/user`;
        console.log('Fetching reviews from:', url);
        console.log('Token:', token);
        
        const response = await fetch(url, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        });
        
        console.log('Response status:', response.status);
        
        if (response.ok) {
            const comments = await response.json();
            console.log('Loaded comments:', comments);
            
            if (comments.length === 0) {
                reviewsList.innerHTML = '<p style="text-align: center; color: #999; padding: 2rem;">You haven\'t reviewed any places yet</p>';
                return;
            }
            
            // Render reviews
            reviewsList.innerHTML = comments.map(comment => {
                const date = new Date(comment.created_at).toLocaleDateString('en-US', {
                    year: 'numeric',
                    month: 'short',
                    day: 'numeric'
                });
                
                // Default image nếu không có
                const placeImage = comment.place_image || 'https://images.unsplash.com/photo-1528127269322-539801943592?q=80&w=2070';
                const placeName = comment.place_name || `Place #${comment.place_id}`;
                
                return `
                    <div class="review-card" data-comment-id="${comment.id}">
                        <div class="review-header">
                            <div class="review-place">
                                <img src="${placeImage}" alt="${placeName}" class="review-place-img">
                                <div class="review-place-info">
                                    <h4>${placeName}</h4>
                                    <p>${date}</p>
                                </div>
                            </div>
                        </div>
                        <div class="review-content">
                            ${comment.content}
                        </div>
                        <div class="review-actions">
                            <button class="btn-view-place" onclick="window.location.href='detail.html?id=${comment.place_id}'">
                                View Place
                            </button>
                            <button class="btn-delete-review" onclick="deleteReview(${comment.id})">
                                Delete
                            </button>
                        </div>
                    </div>
                `;
            }).join('');
        } else {
            const errorText = await response.text();
            console.error('Failed to load reviews:', response.status, errorText);
            
            // Nếu token hết hạn hoặc không hợp lệ, logout và redirect
            if (response.status === 401) {
                alert('Your session has expired. Please login again.');
                localStorage.clear();
                window.location.href = 'login.html';
                return;
            }
            
            reviewsList.innerHTML = `<p style="text-align: center; color: #999; padding: 2rem;">Failed to load reviews (${response.status})</p>`;
        }
    } catch (error) {
        console.error('Error loading reviews:', error);
        reviewsList.innerHTML = '<p style="text-align: center; color: #999; padding: 2rem;">Error loading reviews</p>';
    }
}

// Global function để xóa review
window.deleteReview = async function(commentId) {
    if (!confirm('Are you sure you want to delete this review?')) return;
    
    const token = localStorage.getItem('token');
    
    try {
        const response = await fetch(`${CONFIG.apiBase}/api/v1/comments/${commentId}`, {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (response.ok) {
            // Reload reviews
            loadReviews();
        } else {
            alert('Failed to delete review');
        }
    } catch (error) {
        console.error('Error deleting review:', error);
        alert('Error deleting review');
    }
};

// Initialize liked subtabs
function initLikedSubtabs() {
    const subtabBtns = document.querySelectorAll('.liked-subtab-btn');
    const subtabContents = document.querySelectorAll('.liked-subtab-content');
    
    // Only initialize once
    if (subtabBtns[0]?.dataset.initialized) return;
    
    subtabBtns.forEach(btn => {
        btn.dataset.initialized = 'true';
        btn.addEventListener('click', () => {
            const targetSubtab = btn.dataset.subtab;
            
            // Remove active class from all
            subtabBtns.forEach(b => b.classList.remove('active'));
            subtabContents.forEach(c => c.classList.remove('active'));
            
            // Add active to clicked
            btn.classList.add('active');
            const subtabContent = document.getElementById(`${targetSubtab}-subtab`);
            if (subtabContent) {
                subtabContent.classList.add('active');
            }
            
            // Load content based on subtab
            if (targetSubtab === 'liked-comments') {
                loadLikedComments();
            } else if (targetSubtab === 'liked-places') {
                loadLikedPlaces();
            }
        });
    });
}

// Load liked comments
async function loadLikedComments() {
    const likedCommentsList = document.getElementById('likedCommentsList');
    const token = localStorage.getItem('token');
    
    if (!token) {
        likedCommentsList.innerHTML = '<p style="text-align: center; color: #999; padding: 2rem;">Please login to view liked reviews</p>';
        return;
    }
    
    try {
        likedCommentsList.innerHTML = '<p style="text-align: center; color: #999; padding: 2rem;">Loading liked reviews...</p>';
        
        const response = await fetch(`${CONFIG.apiBase}/api/v1/likes/comments`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (!response.ok) {
            throw new Error('Failed to load liked comments');
        }
        
        const likedComments = await response.json();
        
        if (likedComments.length === 0) {
            likedCommentsList.innerHTML = '<p style="text-align: center; color: #999; padding: 2rem;">You haven\'t liked any reviews yet</p>';
            return;
        }
        
        likedCommentsList.innerHTML = likedComments.map(item => {
            const date = new Date(item.created_at).toLocaleDateString('en-US', {
                year: 'numeric',
                month: 'short',
                day: 'numeric'
            });
            
            const placeImage = item.place_image || 'https://images.unsplash.com/photo-1528127269322-539801943592?q=80&w=2070';
            const placeName = item.place_name || 'Unknown Place';
            
            return `
                <div class="review-card" data-comment-id="${item.comment_id}">
                    <div class="review-header">
                        <div class="review-place">
                            <img src="${placeImage}" alt="${placeName}" class="review-place-img">
                            <div class="review-place-info">
                                <h4>${placeName}</h4>
                                <p>${date}</p>
                            </div>
                        </div>
                    </div>
                    <div class="review-content">
                        ${item.comment_content || 'No content'}
                    </div>
                    <div class="review-actions">
                        <button class="btn-view-place" onclick="window.location.href='detail.html?id=${item.place_id}'">
                            View Place
                        </button>
                        <button class="btn-delete-review" onclick="unlikeComment(${item.comment_id})">
                            Unlike
                        </button>
                    </div>
                </div>
            `;
        }).join('');
    } catch (error) {
        console.error('Error loading liked comments:', error);
        likedCommentsList.innerHTML = '<p style="text-align: center; color: #999; padding: 2rem;">Error loading liked reviews</p>';
    }
}

// Load liked places
async function loadLikedPlaces() {
    const likedPlacesGrid = document.getElementById('likedPlacesGrid');
    const token = localStorage.getItem('token');
    
    if (!token) {
        likedPlacesGrid.innerHTML = '<p style="text-align: center; color: #999; padding: 2rem;">Please login to view liked places</p>';
        return;
    }
    
    try {
        likedPlacesGrid.innerHTML = '<p style="text-align: center; color: #999; padding: 2rem;">Loading liked places...</p>';
        
        const response = await fetch(`${CONFIG.apiBase}/api/v1/likes/places`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (!response.ok) {
            throw new Error('Failed to load liked places');
        }
        
        const likedPlaces = await response.json();
        
        if (likedPlaces.length === 0) {
            likedPlacesGrid.innerHTML = '<p style="text-align: center; color: #999; padding: 2rem;">You haven\'t liked any places yet</p>';
            return;
        }
        
        likedPlacesGrid.innerHTML = likedPlaces.map(place => `
            <div class="place-card" onclick="window.location.href='detail.html?id=${place.place_id}'">
                ${place.place_image ? `<img src="${place.place_image}" alt="${place.place_name}" class="place-card-image">` : ''}
                <div class="place-card-content">
                    <h3 class="place-card-title">${place.place_name}</h3>
                    <div class="place-card-address">
                        <i class="fas fa-map-marker-alt"></i>
                        ${place.place_address || 'No address'}
                    </div>
                    ${place.place_rating ? `
                        <div class="place-card-rating">
                            <i class="fas fa-star"></i>
                            <span>${place.place_rating.toFixed(1)}</span>
                        </div>
                    ` : ''}
                    <div class="place-card-actions">
                        <button class="btn-view-details" onclick="event.stopPropagation(); window.location.href='detail.html?id=${place.place_id}'">
                            <i class="fas fa-info-circle"></i> View Details
                        </button>
                        <button class="btn-unlike-place" onclick="event.stopPropagation(); unlikePlace(${place.place_id})">
                            <i class="fas fa-heart-broken"></i> Unlike
                        </button>
                    </div>
                </div>
            </div>
        `).join('');
    } catch (error) {
        console.error('Error loading liked places:', error);
        likedPlacesGrid.innerHTML = '<p style="text-align: center; color: #999; padding: 2rem;">Error loading liked places</p>';
    }
}

// Unlike a comment
window.unlikeComment = async function(commentId) {
    if (!confirm('Remove this review from your liked list?')) return;
    
    const token = localStorage.getItem('token');
    
    try {
        const response = await fetch(`${CONFIG.apiBase}/api/v1/likes/comment/${commentId}`, {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (response.ok) {
            loadLikedComments();
        } else {
            alert('Failed to unlike review');
        }
    } catch (error) {
        console.error('Error unliking comment:', error);
        alert('Error unliking review');
    }
};

// Unlike a place
window.unlikePlace = async function(placeId) {
    if (!confirm('Remove this place from your liked list?')) return;
    
    const token = localStorage.getItem('token');
    
    try {
        const response = await fetch(`${CONFIG.apiBase}/api/v1/likes/place/${placeId}`, {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (response.ok) {
            loadLikedPlaces();
        } else {
            alert('Failed to unlike place');
        }
    } catch (error) {
        console.error('Error unliking place:', error);
        alert('Error unliking place');
    }
};
