# Tổng kết: Thuật toán tính điểm Rating

## 🎯 Mục tiêu đã hoàn thành

Đã implement thành công thuật toán tính điểm rating giữa user và place theo thang 1-5 điểm với đầy đủ các yêu cầu:

✅ **Thời gian xem (View Time)**
- Dưới 5 giây: Bấm nhầm, không tính điểm
- 5-90 giây: Điểm từ 2.5 đến 4.0 (tỉ lệ tuyến tính)
- Trên 90 giây: 4.0 điểm (max)
- Lần xem sau: Chỉ cập nhật nếu điểm cao hơn điểm hiện tại

✅ **Like/Dislike**
- Like: +4 điểm vào điểm hiện tại
- Dislike: -5 điểm hoặc tối thiểu 1 điểm

✅ **Comment**
- Comment đầu tiên: +0.5 điểm
- Comment sau: Không cộng thêm

✅ **Giới hạn điểm số**
- Tối thiểu: 1.0
- Tối đa: 5.0

## 📁 Files đã tạo/chỉnh sửa

### 1. `backend/app/services/scoring_service.py` ⭐
**Chức năng chính:**
- Class `RatingScorer` với các method tính toán điểm
- `calculate_view_time_score()`: Tính điểm từ thời gian xem
- `calculate_rating_score()`: Tính tổng điểm từ tất cả interactions
- `update_rating()`: Cập nhật/tạo rating trong database

### 2. `backend/app/routers/rating.py` 🔄
**Endpoints mới:**
- `POST /rating/view-time`: Track thời gian xem và cập nhật rating
- `GET /rating/rating/{place_id}`: Lấy rating hiện tại của user

### 3. `backend/app/routers/like.py` 🔄
**Cập nhật:**
- `POST /likes/place`: Tự động cập nhật rating khi like/dislike

### 4. `backend/app/routers/comment.py` 🔄
**Cập nhật:**
- `POST /comments`: Tự động cập nhật rating khi comment (+0.5 điểm cho lần đầu)

### 5. `backend/test_rating_algorithm.py` 📊
**File demo:** Hiển thị cách thuật toán hoạt động với các test cases

### 6. `backend/RATING_ALGORITHM.md` 📖
**Documentation:** Hướng dẫn chi tiết về thuật toán và API

### 7. `backend/INTEGRATION_EXAMPLES.py` 💡
**Ví dụ:** Code mẫu để tích hợp vào frontend

## 🚀 Cách sử dụng

### Backend (đã tích hợp sẵn):

```python
# Tự động chạy khi user:
# 1. Xem place -> POST /rating/view-time
# 2. Like/Dislike -> POST /likes/place
# 3. Comment -> POST /comments
```

### Frontend cần implement:

```javascript
// 1. Track view time
const startTime = Date.now();
window.addEventListener('beforeunload', async () => {
    const viewTimeSeconds = (Date.now() - startTime) / 1000;
    await fetch('/rating/view-time', {
        method: 'POST',
        body: JSON.stringify({
            place_id: currentPlaceId,
            view_time_seconds: viewTimeSeconds
        })
    });
});

// 2. Like/Dislike (đã có sẵn, chỉ cần đảm bảo đang call đúng endpoint)
// POST /likes/place với body: {place_id, is_like}

// 3. Comment (đã có sẵn, chỉ cần đảm bảo đang call đúng endpoint)
// POST /comments với body: {place_id, content}
```

## 📊 Ví dụ thực tế

### Scenario 1: User thích place
```
1. Xem 60 giây     → 3.47 điểm
2. Comment         → 3.97 điểm (+0.5)
3. Like            → 5.0 điểm (+4, max)
```

### Scenario 2: User không thích
```
1. Xem 10 giây     → 2.59 điểm
2. Dislike         → 1.0 điểm (-5, min)
```

### Scenario 3: User đã có rating
```
1. Rating cũ: 3.0  → 3.0 điểm
2. Xem lại 90s     → 4.0 điểm (cao hơn, cập nhật)
3. Comment         → 4.5 điểm (+0.5)
4. Like            → 5.0 điểm (+4, max)
```

## 🧪 Testing

Chạy demo để xem thuật toán:
```bash
cd backend
python test_rating_algorithm.py
```

Output sẽ hiển thị các test cases và ví dụ tính điểm.

## 📋 API Endpoints

| Endpoint | Method | Mô tả |
|----------|--------|-------|
| `/rating/view-time` | POST | Track thời gian xem |
| `/rating/rating/{place_id}` | GET | Lấy rating hiện tại |
| `/likes/place` | POST | Like/Dislike (auto update rating) |
| `/comments` | POST | Tạo comment (auto update rating) |

## ✨ Highlights

1. **Tự động tính toán:** Mọi endpoint đều tự động cập nhật rating score
2. **Không duplicate logic:** Tất cả logic tính toán tập trung trong `RatingScorer`
3. **Dễ maintain:** Code rõ ràng, có comment và documentation đầy đủ
4. **Tested:** Có file demo với nhiều test cases
5. **Well documented:** Có 2 files hướng dẫn (MD và examples)

## 🎓 Technical Details

- **Database:** SQLite (table `rating`)
- **Framework:** FastAPI + SQLModel
- **Score range:** 1.0 - 5.0 (float, 2 decimals)
- **View time tracking:** JavaScript frontend → Backend API
- **Auto integration:** Like/Comment endpoints tự động update rating

## 📝 Notes quan trọng

1. **View time cập nhật thông minh:** 
   - Lần xem đầu tiên: Tạo rating mới
   - Lần xem sau: Chỉ cập nhật nếu điểm cao hơn điểm hiện tại
2. **Comment bonus chỉ 1 lần:** Chỉ comment đầu tiên được +0.5
3. **Bấm nhầm được loại bỏ:** < 5 giây không tính
4. **Score luôn valid:** Clamp trong khoảng [1.0, 5.0]
5. **Thời gian xem tối đa 90 giây:** > 90 giây = 4.0 điểm (capped)

## 🔜 Next Steps

1. **Frontend integration:** 
   - Implement view time tracking
   - Đảm bảo đang call đúng endpoints

2. **Testing:**
   - Test với real users
   - Verify rating scores trong database

3. **Monitoring:**
   - Track average scores
   - Analyze user behavior patterns

4. **Optional enhancements:**
   - Add weights cho different themes
   - Consider time decay (old ratings decay over time)
   - Add explicit ratings (user can rate 1-5 stars manually)

---

**Tất cả code đã sẵn sàng và hoạt động!** 🎉
