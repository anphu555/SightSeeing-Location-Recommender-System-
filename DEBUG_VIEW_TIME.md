# Debug Guide - View Time Tracking

## 🔍 Hướng Dẫn Debug View Time Tracking

Tôi đã thêm các console logs để debug view time tracking. Hãy làm theo các bước sau:

## 📋 Các Bước Test

### Bước 1: Khởi động hệ thống

```powershell
# Backend (Terminal 1)
cd d:\SightSeeing-Location-Recommender-System-\backend
.\start.bat

# Frontend (Terminal 2)
cd d:\SightSeeing-Location-Recommender-System-\frontend\exSighting
npm run dev
```

### Bước 2: Mở Browser với DevTools

1. Mở Chrome/Edge
2. Nhấn **F12** để mở DevTools
3. Chọn tab **Console**
4. Check "Preserve log" để logs không bị xóa khi navigate

### Bước 3: Login

1. Vào `http://localhost:5173/login.html`
2. Login với tài khoản của bạn
3. Xem console, phải thấy token được lưu

### Bước 4: Vào trang results

1. Vào `http://localhost:5173/results.html` hoặc search từ home
2. Xem danh sách địa điểm

### Bước 5: Click vào một địa điểm

1. **Click vào một địa điểm** từ results.html
2. Trang detail.html sẽ load
3. **Xem console**, phải thấy log:

```javascript
[View Time Tracking] Initialized: {
    place_id: 123,
    start_time: "12:34:56",
    token_exists: true
}
```

**✅ Nếu thấy log này → Initialization thành công!**  
**❌ Nếu KHÔNG thấy → Có vấn đề với DOMContentLoaded**

### Bước 6: Chờ 10 giây

Chờ ít nhất 10 giây trên trang detail.

### Bước 7: Đóng tab (hoặc back)

1. **Đóng tab** hoặc nhấn **Back button**
2. **Xem console ngay lập tức**, phải thấy:

```javascript
[View Time Tracking] beforeunload: {
    view_time: 10.5,
    place_id: 123,
    will_send: true
}

[View Time Tracking] Sending request from beforeunload...

[View Time Tracking] Response: 200

[View Time Tracking] Success: {
    user_id: 1,
    place_id: 123,
    score: 2.59,
    status: "created"
}
```

**✅ Nếu thấy các log này → View time tracking hoạt động!**  
**❌ Nếu không thấy hoặc có error → Đọc phần Troubleshooting**

### Bước 8: Kiểm tra Database

```sql
-- Mở SQLite database
cd d:\SightSeeing-Location-Recommender-System-\backend
sqlite3 vietnamtravel.db

-- Query ratings
SELECT 
    r.id,
    r.user_id,
    u.username,
    r.place_id,
    p.name,
    r.score,
    datetime(r.created_at) as created
FROM rating r
JOIN user u ON r.user_id = u.id
JOIN place p ON r.place_id = p.id
ORDER BY r.id DESC
LIMIT 5;
```

**✅ Phải thấy record mới với score tương ứng view time**

## 🐛 Troubleshooting

### Vấn đề 1: Không thấy log "Initialized"

**Nguyên nhân:** DOMContentLoaded không fire hoặc file JS không load

**Giải pháp:**
1. Check xem detail.html có import detail.js không:
   ```html
   <script type="module" src="./src/js/detail.js"></script>
   ```
2. Check console có lỗi JS nào không
3. Hard refresh: **Ctrl + Shift + R**

### Vấn đề 2: token_exists: false

**Nguyên nhân:** Chưa login hoặc token hết hạn

**Giải pháp:**
1. Login lại
2. Check localStorage:
   ```javascript
   console.log(localStorage.getItem('token'));
   ```
3. Nếu null → login lại

### Vấn đề 3: will_send: false

**Nguyên nhân:** View time < 5 giây hoặc currentPlaceId = null

**Giải pháp:**
1. Đảm bảo xem >= 5 giây
2. Check log "Initialized" có place_id đúng không
3. Nếu place_id = null → có bug trong DOMContentLoaded

### Vấn đề 4: Response: 401 Unauthorized

**Nguyên nhân:** Token không hợp lệ hoặc hết hạn

**Giải pháp:**
1. Login lại để lấy token mới
2. Check backend có chạy không
3. Check token format trong localStorage

### Vấn đề 5: Response: 500 Internal Server Error

**Nguyên nhân:** Lỗi backend

**Giải pháp:**
1. Check backend logs/console
2. Check database connection
3. Check API endpoint có tồn tại không:
   ```bash
   curl http://localhost:8000/api/v1/rating/view-time
   ```

### Vấn đề 6: Request bị cancelled

**Nguyên nhân:** Page đóng trước khi request hoàn thành

**Giải pháp:**
- Đã dùng `keepalive: true` ✅
- Nếu vẫn bị cancel → browser có thể chặn
- Test với tab visibility change thay vì close tab

### Vấn đề 7: Không thấy log nào cả

**Nguyên nhân:** "Preserve log" chưa được check trong DevTools

**Giải pháp:**
1. Mở DevTools Console
2. Click icon ⚙️ (Settings)
3. Check ✅ "Preserve log"
4. Test lại

## 📊 Expected Logs Flow

### Luồng hoàn chỉnh khi test thành công:

```javascript
// 1. Khi vào trang detail
[View Time Tracking] Initialized: {
    place_id: 123,
    start_time: "12:34:56",
    token_exists: true
}

// 2. Sau 10 giây, khi đóng tab
[View Time Tracking] beforeunload: {
    view_time: 10.234,
    place_id: 123,
    will_send: true
}

[View Time Tracking] Sending request from beforeunload...

// 3. Backend response
[View Time Tracking] Response: 200

[View Time Tracking] Success: {
    user_id: 1,
    place_id: 123,
    score: 2.59,
    status: "created"
}
```

### Nếu chuyển tab (thay vì đóng):

```javascript
// 1. Khi chuyển sang tab khác
[View Time Tracking] visibilitychange (hidden): {
    view_time: 10.5,
    place_id: 123,
    will_send: true
}

[View Time Tracking] Sending request from visibilitychange...

[View Time Tracking] Response: 200

[View Time Tracking] Success: {...}

// 2. Khi quay lại tab
[View Time Tracking] Tab visible again, timer reset
```

## ✅ Success Criteria

Sau khi test, đảm bảo:

- [x] Thấy log "Initialized" với place_id đúng
- [x] Thấy log "beforeunload" với view_time chính xác
- [x] Thấy log "Sending request..."
- [x] Thấy log "Response: 200"
- [x] Thấy log "Success" với score đúng
- [x] Database có record mới
- [x] Score tính đúng theo view time

## 🎯 Next Steps

Nếu tất cả logs đều xuất hiện đúng:
1. **Remove console.logs** trong production để giảm noise
2. Deploy code lên production
3. Monitor database để xem ratings có được tạo không

Nếu vẫn có vấn đề:
1. Screenshot console logs
2. Export database ratings table
3. Check backend logs
4. Report issue với đầy đủ thông tin

---

**Created:** December 16, 2025  
**Purpose:** Debug view time tracking after clicking from results.html
