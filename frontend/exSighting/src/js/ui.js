import { ApiService } from './api.js';
import { ToastManager } from './toast.js';

// Xử lý logic khi bấm nút Like/Dislike
async function handleRatingAction(placeId, preference, container) {
    try {
        const data = await ApiService.sendRating(placeId, preference);
        
        const likeBtn = container.querySelector('.btn-like');
        const dislikeBtn = container.querySelector('.btn-dislike');
        
        likeBtn.classList.remove('active');
        dislikeBtn.classList.remove('active');
        
        if (preference === 'like') {
            likeBtn.classList.add('active');
            ToastManager.show(`Đã thích địa điểm này! (Score: ${data.score})`, "success");
        } else {
            dislikeBtn.classList.add('active');
            ToastManager.show(`Đã đánh dấu không thích! (Score: ${data.score})`, "success");
        }

    } catch (e) {
        if (e.status === 401 || e.message === "Unauthorized") {
            ToastManager.show("Bạn cần đăng nhập để đánh giá!", "warning");
        } else {
            console.error(e);
            ToastManager.show("Có lỗi xảy ra khi gửi đánh giá.", "error");
        }
    }
}

export const UIManager = {
    createCardElement(item) {
        const div = document.createElement('div');
        div.className = 'card';
        
        const img = document.createElement('img');
        img.src = 'images/halong.jpg'; 
        img.alt = item.name;
        
        const name = document.createElement('p'); 
        name.textContent = item.name;
        
        const meta = document.createElement('p');
        Object.assign(meta.style, { fontWeight: 'normal', color: '#666' });
        meta.textContent = `${item.province ?? ''} • Score: ${parseFloat(item.score).toFixed(2)}`;
    
        const btnContainer = document.createElement('div');
        btnContainer.className = 'rating-buttons';
        btnContainer.dataset.placeId = item.id;
        
        const createBtn = (cls, text, type) => {
            const btn = document.createElement('button');
            btn.className = cls;
            btn.innerHTML = text;
            btn.onclick = () => handleRatingAction(item.id, type, btnContainer);
            return btn;
        };
    
        btnContainer.append(
            createBtn('btn-like', '👍 Like', 'like'),
            createBtn('btn-dislike', '👎 Dislike', 'dislike')
        );
    
        div.append(img, name, meta, btnContainer);
        return div;
    },

    applyUserRatings(ratingsMap) {
        if (!ratingsMap) return;
        document.querySelectorAll('.rating-buttons').forEach(container => {
            const placeId = container.dataset.placeId;
            const score = ratingsMap[placeId];
      
            if (score !== undefined) {
                const likeBtn = container.querySelector('.btn-like');
                const dislikeBtn = container.querySelector('.btn-dislike');
                
                likeBtn.classList.remove('active');
                dislikeBtn.classList.remove('active');
                
                if (score >= 4.0) likeBtn.classList.add('active');
                else if (score <= 2.0) dislikeBtn.classList.add('active');
            }
        });
    }
};