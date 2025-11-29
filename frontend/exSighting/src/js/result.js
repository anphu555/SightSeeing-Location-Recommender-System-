document.addEventListener('DOMContentLoaded', () => {
  // --- CẤU HÌNH API (Sửa 1 chỗ duy nhất tại đây) ---
  const apiBase = 'http://localhost:8000'; 
  
  const params  = new URLSearchParams(location.search);
  
  // Toast notification function - accessible alternative to alert()
  function showToast(message, type = 'info', duration = 4000) {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.setAttribute('role', 'status');
    
    const icons = {
      success: '✓',
      error: '✕',
      warning: '⚠',
      info: 'ℹ'
    };
    
    const iconSpan = document.createElement('span');
    iconSpan.className = 'toast-icon';
    iconSpan.textContent = icons[type] || icons.info;
    
    const messageSpan = document.createElement('span');
    messageSpan.className = 'toast-message';
    messageSpan.textContent = message;
    
    const closeBtn = document.createElement('button');
    closeBtn.className = 'toast-close';
    closeBtn.setAttribute('aria-label', 'Close notification');
    closeBtn.textContent = '×';
    closeBtn.addEventListener('click', () => removeToast(toast));
    
    toast.appendChild(iconSpan);
    toast.appendChild(messageSpan);
    toast.appendChild(closeBtn);
    
    container.appendChild(toast);
    
    const timeoutId = setTimeout(() => removeToast(toast), duration);
    toast._timeoutId = timeoutId;
  }
  
  function removeToast(toast) {
    if (!toast.parentElement) return;
    if (toast._timeoutId) {
      clearTimeout(toast._timeoutId);
    }
    toast.style.animation = 'fadeOut 0.3s ease-out forwards';
    setTimeout(() => toast.remove(), 300);
  }
  
  // Lấy text tìm kiếm
  const text = (params.get('text') || '').trim();
  
  // Khởi tạo số lượng k ban đầu
  let currentK = Number(params.get('k') || '6');
  const stepK  = 6; 
  
  let isLoading = false; 
  let isFull    = false; 

  // DOM Elements
  const headerH2      = document.querySelector('.results-header h2');
  const cardsContainer= document.querySelector('.cards');
  const loader        = document.querySelector('.loading-indicator');
  const headerInput   = document.querySelector('.search-bar input');
  const headerBtn     = document.querySelector('.search-bar button');

  if (headerInput) headerInput.value = text;

  // Hàm tạo thẻ HTML cho 1 địa điểm
  function renderCard(item){
    const div = document.createElement('div');
    div.className = 'card';
    const img = document.createElement('img');
    img.src = 'images/halong.jpg'; 
    img.alt = item.name;
    
    const name = document.createElement('p'); 
    name.textContent = item.name;
    
    const meta = document.createElement('p');
    meta.style.fontWeight='normal'; 
    meta.style.color='#666'; 
    meta.textContent = `${item.province ?? ''} • Score: ${parseFloat(item.score).toFixed(2)}`;

    const btnContainer = document.createElement('div');
    btnContainer.className = 'rating-buttons';
    btnContainer.dataset.placeId = item.id;
    
    const likeBtn = document.createElement('button');
    likeBtn.className = 'btn-like';
    likeBtn.innerHTML = '👍 Like';
    likeBtn.onclick = () => handleRating(item.id, 'like', btnContainer);
    
    const dislikeBtn = document.createElement('button');
    dislikeBtn.className = 'btn-dislike';
    dislikeBtn.innerHTML = '👎 Dislike';
    dislikeBtn.onclick = () => handleRating(item.id, 'dislike', btnContainer);
    
    btnContainer.appendChild(likeBtn);
    btnContainer.appendChild(dislikeBtn);

    div.append(img, name, meta, btnContainer);
    return div;
  }

  // --- HÀM XỬ LÝ ĐÁNH GIÁ ---
  async function handleRating(placeId, preference, container) {
      const token = localStorage.getItem('token');
      if (!token) {
          showToast("Bạn cần đăng nhập để đánh giá!", "warning");
          window.location.href = "login.html";
          return;
      }

      try {
          const res = await fetch(`${apiBase}/api/v1/user/rate`, {
              method: 'POST',
              headers: { 
                  'Content-Type': 'application/json',
                  'Authorization': `Bearer ${token}`
              },
              body: JSON.stringify({ place_id: placeId, preference: preference })
          });

          if (res.ok) {
              const likeBtn = container.querySelector('.btn-like');
              const dislikeBtn = container.querySelector('.btn-dislike');
              
              // Reset both buttons
              likeBtn.classList.remove('active');
              dislikeBtn.classList.remove('active');
              
              // Activate the selected button
              if (preference === 'like') {
                  likeBtn.classList.add('active');
                  showToast("Đã thích địa điểm này!", "success");
              } else if (preference === 'dislike') {
                  dislikeBtn.classList.add('active');
                  showToast("Đã đánh dấu không thích!", "success");
              }
          } else {
              if (res.status === 401) {
                  showToast("Phiên đăng nhập hết hạn. Vui lòng đăng nhập lại.", "error");
                  window.location.href = "login.html";
              } else {
                  showToast("Có lỗi xảy ra khi gửi đánh giá.", "error");
              }
          }
      } catch (e) {
          console.error(e);
          showToast("Không thể kết nối tới server.", "error");
      }
  }

  // Hàm gọi API chính
  async function fetchResults(kValue, isLoadMore = false) {
    if (!text) {
      headerH2.textContent = '0 results';
      return;
    }
    
    if (!isLoadMore) {
      headerH2.textContent = 'Loading...';
      cardsContainer.innerHTML = ''; 
    } else {
      loader.classList.add('active'); 
    }

    isLoading = true;

    try {
// 1. Lấy token từ localStorage
      const token = localStorage.getItem('token');
      
      // 2. Chuẩn bị headers
      const headers = { 
        'Content-Type': 'application/json' 
      };

      // 3. Nếu có token (đã đăng nhập), đính kèm vào header Authorization
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }

      // 4. Gọi fetch với headers mới
      const r = await fetch(`${apiBase}/api/v1/recommend`, {
        method: 'POST',
        headers: headers, // <--- Dùng biến headers vừa tạo
        body: JSON.stringify({ user_text: text, top_k: kValue })
      });
      // --------------------

      if (!r.ok) throw new Error(`HTTP ${r.status}`);

      const data = await r.json();
      const items = data.results || [];

      if (!isLoadMore) {
        headerH2.textContent = `${items.length} results`;
        items.forEach(it => cardsContainer.appendChild(renderCard(it)));
      } else {
        const oldLength = currentK - stepK; 
        const newItems = items.slice(oldLength); 

        if (newItems.length === 0) {
          isFull = true; 
          loader.textContent = "Đã hiển thị hết kết quả.";
        } else {
          newItems.forEach(it => cardsContainer.appendChild(renderCard(it)));
          headerH2.textContent = `${items.length} results`; 
        }
      }

    } catch (e) {
      console.error(e);
      if (!isLoadMore) {
        headerH2.textContent = 'Error loading data';
        cardsContainer.innerHTML = `<div style="color:red; padding:10px">${e.message}</div>`;
      }
    } finally {
      isLoading = false;
      loader.classList.remove('active');
    }
  }

  // --- HÀM MỚI: Tải lại lịch sử đánh giá ---
  async function loadUserRatings() {
      const token = localStorage.getItem('token');
      if (!token) return;

      try {
          const res = await fetch(`${apiBase}/api/v1/user/my-ratings`, {
              method: 'GET',
              headers: { 
                  'Authorization': `Bearer ${token}`
              }
          });

          if (res.ok) {
              const ratingsMap = await res.json(); 
              
              document.querySelectorAll('.rating-buttons').forEach(container => {
                  const placeId = container.dataset.placeId;
                  
                  if (ratingsMap[placeId]) {
                      const score = ratingsMap[placeId];
                      const likeBtn = container.querySelector('.btn-like');
                      const dislikeBtn = container.querySelector('.btn-dislike');
                      
                      // Reset
                      likeBtn.classList.remove('active');
                      dislikeBtn.classList.remove('active');
                      
                      // Set active based on score: 1 = like, -1 = dislike
                      if (score === 1) {
                          likeBtn.classList.add('active');
                      } else if (score === -1) {
                          dislikeBtn.classList.add('active');
                      }
                  }
              });
          }
      } catch (e) {
          console.error("Lỗi tải lịch sử đánh giá:", e);
      }
  }

  // Chạy lần đầu tiên
  (async () => {
        await fetchResults(currentK, false);
        await loadUserRatings();
    })();

  window.addEventListener('scroll', () => {
    if (isLoading || isFull) return;
    if ((window.innerHeight + window.scrollY) >= document.body.offsetHeight - 100) {
      currentK += stepK; 
      fetchResults(currentK, true); 
    }
  });

  function triggerSearch() {
    const q = (headerInput?.value || '').trim();
    if (!q) return;
    const newParams = new URLSearchParams();
    newParams.set('text', q);
    newParams.set('k', '6'); 
    window.location.search = newParams.toString();
  }

  headerBtn?.addEventListener('click', triggerSearch);
  headerInput?.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') triggerSearch();
  });
});