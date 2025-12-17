# View Time Tracking - Bug Fix Summary

**Date:** December 16, 2025  
**Status:** ✅ FIXED

## 🐛 Vấn Đề

View time tracking không hoạt động - không thể đo thời gian truy cập và tính rating.

## 🔍 Nguyên Nhân

### Bug #1: Token Key Sai ❌
```javascript
// Code cũ (SAI)
const token = localStorage.getItem('access_token'); // ❌ Token không tồn tại với key này

// Code thực tế trong login.js
localStorage.setItem('token', data.access_token); // ✅ Token được lưu với key 'token'
```

**Kết quả:** Function luôn trả về sớm vì `token === null`, không gửi được request lên backend.

### Bug #2: Event Handling Không Tối Ưu
- Function `sendViewTime()` bất đồng bộ nhưng được gọi trong `beforeunload` - không đảm bảo hoàn thành
- Không reset timer khi tab visible trở lại
- Logic phức tạp và khó maintain

### Bug #3: sendBeacon Không Hỗ Trợ Custom Headers
- `navigator.sendBeacon()` không cho phép set Authorization header
- Backend API yêu cầu JWT token trong header

## ✅ Giải Pháp

### Fix #1: Đổi Token Key
```javascript
// ✅ FIXED
const token = localStorage.getItem('token'); // Đúng key được dùng trong login.js
```

### Fix #2: Simplified Event Handlers
```javascript
// Xóa function sendViewTime() không cần thiết
// Đưa logic trực tiếp vào event listeners

// ✅ Thêm reset timer
document.addEventListener('visibilitychange', () => {
    if (document.hidden && currentPlaceId) {
        // Send view time...
        viewStartTime = Date.now(); // ✅ Reset cho lần xem tiếp theo
    } else if (!document.hidden) {
        viewStartTime = Date.now(); // ✅ Reset khi tab visible trở lại
    }
});
```

### Fix #3: Dùng Fetch với keepalive
```javascript
// ✅ FIXED: Dùng fetch thay vì sendBeacon
fetch(`${CONFIG.apiBase}/api/v1/rating/view-time`, {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}` // ✅ Có thể set custom headers
    },
    body: JSON.stringify({
        place_id: currentPlaceId,
        view_time_seconds: Math.round(viewTimeSeconds * 100) / 100
    }),
    keepalive: true // ✅ Đảm bảo request hoàn thành ngay cả khi page unload
});
```

## 📝 Files Modified

1. **[detail.js](frontend/exSighting/src/js/detail.js)**
   - Đổi `'access_token'` → `'token'` (line ~22)
   - Xóa function `sendViewTime()` 
   - Cải thiện `beforeunload` event handler
   - Cải thiện `visibilitychange` event handler với timer reset
   - Dùng `fetch` với `keepalive: true` thay vì `sendBeacon`

2. **[VIEW_TIME_TRACKING.md](frontend/VIEW_TIME_TRACKING.md)**
   - Cập nhật documentation với bug fixes
   - Thêm section "Các lỗi đã sửa"
   - Cập nhật code examples

3. **[TESTING_VIEW_TIME_FIX.md](TESTING_VIEW_TIME_FIX.md)** (NEW)
   - Hướng dẫn chi tiết để test fix
   - Debugging tips
   - Expected scores table

## 🧪 Cách Test

### Quick Test
1. Login vào hệ thống
2. Vào trang detail của một địa điểm (ví dụ: `detail.html?id=1`)
3. Chờ 10 giây
4. Đóng tab
5. Check database:
   ```sql
   SELECT * FROM rating WHERE place_id = 1 ORDER BY id DESC LIMIT 1;
   ```
6. Phải có record mới với score ≈ 2.59 ✅

### Test Page
Mở `view-time-test.html` để test mà không cần database:
- Timer đếm real-time
- Predicted score tính theo công thức
- Log các milestones (5s, 30s, 60s, 90s)

## 📊 Impact

**Trước Fix:**
- ❌ View time = 0 records tracked
- ❌ Rating không được cập nhật
- ❌ Recommendation không cải thiện

**Sau Fix:**
- ✅ View time tracked chính xác (>= 5 giây)
- ✅ Rating tự động cập nhật (2.5 → 4.0)
- ✅ Recommendation cải thiện theo behavior

## 🎯 Algorithm

**View Time → Score Mapping:**
```
if (viewTime < 5s):
    return None  # Bấm nhầm, không track

if (viewTime >= 90s):
    return 4.0   # Max score

# Linear interpolation: 2.5 → 4.0 for 5s → 90s
score = 2.5 + ((viewTime - 5) / 85) * 1.5
```

**Examples:**
- 5s → 2.50
- 30s → 2.94
- 60s → 3.47
- 90s+ → 4.00

## ✅ Checklist

- [x] Bug identified (token key mismatch)
- [x] Fix implemented (changed to correct key)
- [x] Event handlers simplified
- [x] Timer reset logic added
- [x] Used fetch with keepalive
- [x] Removed unused function
- [x] Updated documentation
- [x] Created test guide
- [x] No errors in detail.js

## 🚀 Status

**READY TO TEST AND DEPLOY** ✅

---

**Tested By:** _[Pending Test]_  
**Deployed:** _[Pending]_
