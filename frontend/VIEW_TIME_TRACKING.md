# View Time Tracking Implementation

## ✅ Đã cài đặt và FIX LỖI (Dec 16, 2025)

Tracking thời gian xem đã được thêm vào **detail.html** (trang chi tiết địa điểm) và **đã sửa lỗi token key**.

## 🐛 Các lỗi đã sửa

### 1. **Token Key Inconsistency** ❌ → ✅
- **Lỗi cũ:** Trong hàm `sendViewTime()` sử dụng `localStorage.getItem('access_token')` 
- **Vấn đề:** Token thực tế được lưu với key `'token'` trong login.js
- **Kết quả:** View time tracking không hoạt động vì không tìm thấy token
- **Đã sửa:** Đổi thành `localStorage.getItem('token')` để nhất quán

### 2. **Simplified Event Handling** ✅
- **Xóa:** Function `sendViewTime()` không cần thiết
- **Cải thiện:** Đưa logic trực tiếp vào event listeners để dễ bảo trì
- **Thêm:** Reset timer khi tab visible trở lại để tracking chính xác hơn

### 3. **Better Reliability** ✅
- **Sử dụng:** `fetch` với `keepalive: true` thay vì `sendBeacon` 
- **Lý do:** `sendBeacon` không hỗ trợ custom headers (Authorization Bearer token)
- **Kết quả:** Request được gửi đúng với authentication header

## 📋 Cách hoạt động

### 1. Khi user mở trang detail
```javascript
// Khi load trang detail.html?id=123
currentPlaceId = 123
viewStartTime = Date.now() // Bắt đầu đếm
```

### 2. Khi user rời trang (beforeunload)
```javascript
// Tính thời gian đã xem
viewTimeSeconds = (Date.now() - viewStartTime) / 1000

// Nếu >= 5 giây, gửi lên backend
if (viewTimeSeconds >= 5) {
    fetch(`${CONFIG.apiBase}/api/v1/rating/view-time`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`  // ✅ Sử dụng token đúng
        },
        body: JSON.stringify({
            place_id: 123,
            view_time_seconds: 45.67
        }),
        keepalive: true  // ✅ Đảm bảo request hoàn thành
    });
}
```

### 3. Khi user chuyển tab (visibilitychange)
```javascript
// Khi tab bị ẩn (user chuyển sang tab khác)
if (document.hidden) {
    // Gửi view time nếu >= 5 giây
    // Reset timer cho lần xem tiếp theo
    viewStartTime = Date.now();
}

// Khi tab hiện lại
if (!document.hidden) {
    // Reset timer để đếm lại từ đầu
    viewStartTime = Date.now();
}
```

### 4. Các trường hợp gửi dữ liệu

✅ **User đóng tab/cửa sổ** → `beforeunload` event  
✅ **User chuyển sang tab khác** → `visibilitychange` event (hidden)  
✅ **User nhấn Back/Forward** → `beforeunload` event  
✅ **User navigate sang trang khác** → `beforeunload` event

## 🔧 Code đã sửa

File: `frontend/exSighting/src/js/detail.js`

```javascript
// === VIEW TIME TRACKING ===
let viewStartTime = Date.now();
let currentPlaceId = null;

// Track view time when user leaves the page
window.addEventListener('beforeunload', (event) => {
    const viewTimeSeconds = (Date.now() - viewStartTime) / 1000;
    if (viewTimeSeconds >= 5 && currentPlaceId) {
        const token = localStorage.getItem('token');  // ✅ Fixed: was 'access_token'
        if (token) {
            fetch(`${CONFIG.apiBase}/api/v1/rating/view-time`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({
                    place_id: currentPlaceId,
                    view_time_seconds: Math.round(viewTimeSeconds * 100) / 100
                }),
                keepalive: true  // ✅ Critical for beforeunload
            }).catch(err => {
                console.log('View time tracking:', err.message);
            });
        }
    }
});

// Also track when visibility changes (user switches tab)
document.addEventListener('visibilitychange', () => {
    if (document.hidden && currentPlaceId) {
        const viewTimeSeconds = (Date.now() - viewStartTime) / 1000;
        if (viewTimeSeconds >= 5) {
            const token = localStorage.getItem('token');  // ✅ Fixed
            if (token) {
                fetch(`${CONFIG.apiBase}/api/v1/rating/view-time`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${token}`
                    },
                    body: JSON.stringify({
                        place_id: currentPlaceId,
                        view_time_seconds: Math.round(viewTimeSeconds * 100) / 100
                    }),
                    keepalive: true
                }).catch(err => console.log('View time tracking:', err.message));
                
                // ✅ Reset timer for next viewing session
                viewStartTime = Date.now();
            }
        }
    } else if (!document.hidden) {
        // ✅ When tab becomes visible again, reset timer
        viewStartTime = Date.now();
    }
});
```

## 🧪 Cách test

### Test 1: View time tracking
1. Login vào hệ thống
2. Vào trang detail của một địa điểm (vd: `detail.html?id=1`)
3. Chờ 10 giây
4. Đóng tab
5. Kiểm tra trong database:

```sql
SELECT * FROM rating WHERE place_id = 1 ORDER BY id DESC LIMIT 1;
-- Kết quả: score khoảng 2.59 (tương ứng 10 giây)
```

### Test 2: Bấm nhầm (< 5s)
1. Vào trang detail
2. Đóng ngay (< 5 giây)
3. Kiểm tra database → **Không có record mới** ✅

### Test 3: Xem lâu (90s)
1. Vào trang detail
2. Chờ 90 giây
3. Đóng tab
4. Check database → score = **4.0** (max) ✅

### Test 4: Xem lại với điểm cao hơn
1. User đã có rating = 3.0
2. Vào lại trang detail
3. Chờ 90 giây (điểm mới = 4.0)
4. Đóng tab
5. Check database → score cập nhật lên **4.0** ✅

### Test 5: Xem lại với điểm thấp hơn
1. User đã có rating = 4.0
2. Vào lại trang detail
3. Chờ 30 giây (điểm mới = 2.94)
4. Đóng tab
5. Check database → score vẫn là **4.0** (không đổi) ✅

## 📊 Monitoring

Để kiểm tra view time tracking hoạt động, bạn có thể:

### 1. Console Log
Mở Developer Tools (F12) và xem tab Console khi đóng trang.

### 2. Network Tab
Xem request `POST /api/v1/rating/view-time` được gửi đi.

### 3. Backend Log
Check backend console để thấy request đến.

### 4. Database Query
```sql
-- Xem tất cả ratings được tạo từ view time
SELECT 
    r.id,
    r.user_id,
    u.username,
    r.place_id,
    p.name as place_name,
    r.score,
    CASE 
        WHEN r.score >= 2.5 AND r.score < 2.6 THEN '~5s'
        WHEN r.score >= 2.9 AND r.score < 3.0 THEN '~30s'
        WHEN r.score >= 3.4 AND r.score < 3.5 THEN '~60s'
        WHEN r.score = 4.0 THEN '~90s+'
        ELSE 'other'
    END as estimated_view_time
FROM rating r
JOIN user u ON r.user_id = u.id
JOIN place p ON r.place_id = p.id
ORDER BY r.id DESC
LIMIT 20;
```

## ⚠️ Lưu ý

1. **Cần đăng nhập:** View time chỉ track cho user đã login
2. **Chỉ track detail page:** results.html không track (vì user không đọc kỹ ở đó)
3. **Không block navigation:** Nếu API fail, vẫn cho phép user rời trang
4. **Sử dụng keepalive:** Đảm bảo request được gửi ngay cả khi page đang unload

## 🚀 Next Steps (Optional)

1. **Analytics Dashboard:** Hiển thị average view time per place
2. **Heatmap:** Xem places nào được xem lâu nhất
3. **A/B Testing:** Test xem thay đổi UI có tăng view time không
4. **Engagement Score:** Kết hợp view time + like + comment thành engagement score tổng thể

## 📝 Summary

✅ View time tracking được cài đặt ở `detail.html`  
✅ Chỉ gửi dữ liệu khi >= 5 giây  
✅ Tự động cập nhật rating score theo thuật toán  
✅ Hỗ trợ multiple events (beforeunload, visibilitychange)  
✅ Không block user navigation  

**Status: READY TO USE** 🎉
