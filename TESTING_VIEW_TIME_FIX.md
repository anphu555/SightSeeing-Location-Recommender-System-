# Hướng Dẫn Kiểm Thử View Time Tracking Fix

## 🐛 Lỗi Đã Sửa

View time tracking không hoạt động do:
1. **Sử dụng sai token key**: Code dùng `'access_token'` nhưng token thực tế lưu với key `'token'`
2. **Event handling không tối ưu**: Logic phức tạp và thiếu reset timer
3. **sendBeacon không hỗ trợ Authorization header**: Cần dùng `fetch` với `keepalive`

## ✅ Đã Fix

1. ✅ Đổi `localStorage.getItem('access_token')` → `localStorage.getItem('token')`
2. ✅ Simplified event handlers và thêm logic reset timer
3. ✅ Dùng `fetch` với `keepalive: true` cho cả `beforeunload` và `visibilitychange`
4. ✅ Reset timer khi tab visible trở lại

## 📝 Các Bước Test

### Test 1: Kiểm tra token được lưu đúng key

```javascript
// Mở DevTools Console (F12) sau khi login
console.log('Token:', localStorage.getItem('token'));
// Nếu có output → Token tồn tại ✅
// Nếu null → Chưa login ❌
```

### Test 2: Test View Time Tracking Cơ Bản

1. **Login vào hệ thống**
   - Vào `login.html` và đăng nhập
   - Kiểm tra console: `localStorage.getItem('token')` phải có giá trị

2. **Vào trang detail của một địa điểm**
   - Ví dụ: `detail.html?id=1`
   - Mở DevTools Console (F12)

3. **Chờ ít nhất 10 giây** (để vượt qua threshold 5 giây)

4. **Đóng tab hoặc navigate sang trang khác**

5. **Kiểm tra trong database:**
   ```sql
   SELECT * FROM rating 
   WHERE place_id = 1 
   ORDER BY id DESC 
   LIMIT 1;
   ```
   - Phải có 1 record mới với score khoảng 2.59 (tương ứng ~10 giây)

### Test 3: Test với View Time Test Page

1. **Mở file test:**
   - Navigate tới: `http://localhost:5173/view-time-test.html`
   - Trang này sẽ mô phỏng view time tracking

2. **Quan sát timer:**
   - Timer đếm từ 00:00
   - Predicted Score tăng dần
   - "Will Send?" chuyển từ "No" → "Yes" sau 5 giây

3. **Click "Simulate Send Data":**
   - Check console log để xem dữ liệu sẽ được gửi
   - Score phải tính đúng theo công thức:
     - 5s → 2.5
     - 30s → ~2.94
     - 60s → ~3.47
     - 90s+ → 4.0

### Test 4: Test Visibilitychange (Chuyển Tab)

1. **Login và vào detail page**
2. **Chờ 10 giây**
3. **Chuyển sang tab khác** (hoặc minimize browser)
4. **Chờ 2-3 giây rồi quay lại tab**
5. **Chờ thêm 10 giây nữa**
6. **Đóng tab**
7. **Check database:**
   - Phải có **2 records** cho cùng user_id và place_id
   - Record 1: view_time ~10s (khi chuyển tab)
   - Record 2: view_time ~10s (khi đóng tab)

### Test 5: Test Bấm Nhầm (< 5 giây)

1. **Login và vào detail page**
2. **Đóng ngay lập tức** (trong 5 giây)
3. **Check database:**
   - **KHÔNG có record mới** ✅ (vì < 5 giây)

### Test 6: Test Max Score (90 giây)

1. **Login và vào detail page**
2. **Chờ 90 giây** (hoặc lâu hơn)
3. **Đóng tab**
4. **Check database:**
   - Score phải = **4.0** (max score) ✅

## 🔍 Debugging Tips

### 1. Check Console Logs

Mở DevTools Console và xem các logs:

```javascript
// View time tracking sẽ log errors nếu có
// Ví dụ: "View time tracking: Failed to fetch"
```

### 2. Check Network Tab

1. Mở DevTools → Network tab
2. Vào detail page và chờ 10 giây
3. Đóng tab (hoặc chuyển tab)
4. Check request: `POST /api/v1/rating/view-time`
   - Status phải là **200 OK**
   - Request Headers phải có: `Authorization: Bearer <token>`
   - Request Payload: `{place_id: 1, view_time_seconds: 10.25}`

### 3. Check Backend Logs

Nếu backend đang chạy, check console output:
```
INFO:     POST /api/v1/rating/view-time 200 OK
```

### 4. Common Issues

**❌ Request bị cancelled:**
- Nguyên nhân: Trang đóng trước khi request hoàn thành
- Fix: Đã dùng `keepalive: true` ✅

**❌ 401 Unauthorized:**
- Nguyên nhân: Token không hợp lệ hoặc hết hạn
- Fix: Login lại

**❌ Token null:**
- Nguyên nhân: Chưa login hoặc token key sai
- Fix: Đã sửa token key từ `'access_token'` → `'token'` ✅

**❌ Không có record mới trong DB:**
- Check xem view time có >= 5 giây không
- Check xem user đã login chưa
- Check console logs để xem có lỗi không

## 📊 Expected Scores

| View Time | Score |
|-----------|-------|
| < 5s      | (không lưu) |
| 5s        | 2.50  |
| 10s       | 2.59  |
| 20s       | 2.76  |
| 30s       | 2.94  |
| 45s       | 3.21  |
| 60s       | 3.47  |
| 75s       | 3.74  |
| 90s+      | 4.00  |

## 🎯 Success Criteria

✅ User login thành công và token tồn tại  
✅ View time >= 5 giây được track  
✅ View time < 5 giây không được track  
✅ Score tính đúng theo công thức (2.5 → 4.0)  
✅ Request gửi kèm Authorization header  
✅ Chuyển tab → gửi data và reset timer  
✅ Đóng tab → gửi data với keepalive  
✅ Database có record mới với score đúng  

## 🚀 Next Steps

Sau khi test thành công:

1. **Deploy to production:**
   - Commit và push code changes
   - Build frontend: `cd frontend/exSighting && npm run build`
   - Restart backend if needed

2. **Monitor in production:**
   - Check logs để xem có errors không
   - Query database để xem ratings có được tạo không
   - Analyze view time patterns

3. **Optional improvements:**
   - Add analytics dashboard để visualize view times
   - Add heatmap để xem places nào được xem lâu nhất
   - Combine với like/comment để tạo engagement score tổng thể

## 📞 Support

Nếu vẫn gặp vấn đề:
1. Check console logs (F12)
2. Check network tab để xem request/response
3. Check backend logs
4. Verify token với: `console.log(localStorage.getItem('token'))`
5. Test lại với view-time-test.html page

---

**Last Updated:** December 16, 2025  
**Status:** ✅ FIXED AND READY TO TEST
