# View Time Tracking - Debug Enhancement

**Date:** December 16, 2025  
**Issue:** View time không được tính khi click từ results.html sang detail.html

## 🔍 Những gì đã thêm

Để debug vấn đề view time tracking không hoạt động khi navigate từ results.html, tôi đã thêm **comprehensive console logging** vào tất cả các điểm quan trọng:

### 1. Initialization Logging

```javascript
console.log('[View Time Tracking] Initialized:', {
    place_id: currentPlaceId,
    start_time: new Date(viewStartTime).toLocaleTimeString(),
    token_exists: !!localStorage.getItem('token')
});
```

**Mục đích:** Xác nhận rằng:
- `currentPlaceId` được set đúng
- `viewStartTime` được reset khi vào trang
- Token tồn tại để gửi request

### 2. beforeunload Event Logging

```javascript
console.log('[View Time Tracking] beforeunload:', {
    view_time: viewTimeSeconds,
    place_id: currentPlaceId,
    will_send: viewTimeSeconds >= 5 && !!currentPlaceId
});
```

**Mục đích:** Debug xem:
- View time được tính chính xác không
- place_id có giá trị không (không phải null)
- Có đủ điều kiện để gửi request không

### 3. visibilitychange Event Logging

```javascript
console.log('[View Time Tracking] visibilitychange (hidden):', {
    view_time: viewTimeSeconds,
    place_id: currentPlaceId,
    will_send: viewTimeSeconds >= 5
});
```

**Mục đích:** Track khi user chuyển tab

### 4. Request Sending Logs

```javascript
console.log('[View Time Tracking] Sending request from beforeunload...');
```

**Mục đích:** Xác nhận fetch request được gọi

### 5. Response Logs

```javascript
.then(response => {
    console.log('[View Time Tracking] Response:', response.status);
    return response.json();
})
.then(data => {
    console.log('[View Time Tracking] Success:', data);
})
```

**Mục đích:** 
- Xem status code (200, 401, 500, etc.)
- Xem response data từ backend
- Verify rating được tạo/cập nhật

### 6. Error Logs

```javascript
.catch(err => {
    console.log('[View Time Tracking] Error:', err.message);
})
```

**Mục đích:** Catch và log bất kỳ lỗi nào

## 📝 Files Modified

- **[detail.js](frontend/exSighting/src/js/detail.js)** - Thêm 8 console.log statements
- **[DEBUG_VIEW_TIME.md](DEBUG_VIEW_TIME.md)** - Hướng dẫn debug chi tiết

## 🧪 Cách Test

### Quick Test Steps:

1. **Khởi động hệ thống**
   ```bash
   # Backend
   cd backend && .\start.bat
   
   # Frontend  
   cd frontend\exSighting && npm run dev
   ```

2. **Mở DevTools Console (F12)**
   - Check ✅ "Preserve log"

3. **Login vào hệ thống**

4. **Vào results.html → Click địa điểm**

5. **Xem console logs:**
   ```
   [View Time Tracking] Initialized: {...}
   ```

6. **Chờ 10 giây → Đóng tab**

7. **Xem console logs:**
   ```
   [View Time Tracking] beforeunload: {...}
   [View Time Tracking] Sending request...
   [View Time Tracking] Response: 200
   [View Time Tracking] Success: {...}
   ```

8. **Check database:**
   ```sql
   SELECT * FROM rating ORDER BY id DESC LIMIT 1;
   ```

## 🎯 Expected Logs

### Khi mọi thứ hoạt động đúng:

```javascript
// Step 1: Page load
[View Time Tracking] Initialized: {
    place_id: 123,
    start_time: "14:30:45",
    token_exists: true
}

// Step 2: After 10s, close tab
[View Time Tracking] beforeunload: {
    view_time: 10.234,
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

## 🐛 Possible Issues & Solutions

| Issue | Logs You'll See | Solution |
|-------|----------------|----------|
| **Không init** | Không có log "Initialized" | Check detail.js có được load không, hard refresh |
| **Token null** | `token_exists: false` | Login lại |
| **Place ID null** | `place_id: null` | Bug trong DOMContentLoaded, check URL params |
| **View time < 5s** | `will_send: false` | Chờ lâu hơn trước khi đóng tab |
| **401 Error** | `Response: 401` | Token hết hạn, login lại |
| **500 Error** | `Response: 500` | Backend error, check backend logs |
| **Request cancelled** | Không có log "Response" | Đã dùng keepalive, có thể browser chặn |
| **No logs at all** | Không log nào | "Preserve log" chưa được check |

## 📊 Debug Checklist

Sau khi test, verify:

- [ ] Log "Initialized" xuất hiện với place_id đúng
- [ ] Log "beforeunload" xuất hiện với view_time chính xác
- [ ] `will_send: true` khi view time >= 5s
- [ ] Log "Sending request" xuất hiện
- [ ] Log "Response: 200" xuất hiện
- [ ] Log "Success" với score đúng
- [ ] Database có record mới
- [ ] Score match với view time (2.5-4.0 range)

## ⚡ Performance Note

Các console.log này chỉ nên dùng cho **development/debugging**.

Khi đã xác nhận mọi thứ hoạt động:
1. Comment out hoặc remove các console.log
2. Hoặc wrap trong condition:
   ```javascript
   const DEBUG = false;
   if (DEBUG) console.log(...);
   ```

## 🚀 Next Actions

1. **Test với hướng dẫn trong DEBUG_VIEW_TIME.md**
2. **Quan sát console logs**
3. **Identify exact issue** dựa vào logs
4. **Report findings:** 
   - Logs nào xuất hiện?
   - Logs nào không xuất hiện?
   - Error messages (nếu có)?
   - Database state?

---

**Status:** 🔍 DEBUG MODE ACTIVE  
**Purpose:** Identify why view time tracking doesn't work when navigating from results.html  
**Next:** Run test and analyze console logs
