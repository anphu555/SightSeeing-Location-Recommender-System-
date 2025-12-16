# Thuật Toán Tính Điểm Rating (User-Place)

## Tổng quan

Hệ thống tính điểm rating giữa user và place theo thang **1.0 - 5.0** (có thể có số thập phân), dựa trên các tương tác của người dùng:
- Thời gian xem (view time)
- Like/Dislike
- Comment

## Quy tắc tính điểm

### 1. Thời gian xem (View Time)

Tính theo giây:

| Thời gian | Điểm số | Mô tả |
|-----------|---------|-------|
| < 5 giây | Không tính | Bấm nhầm, không thay đổi điểm |
| 5 giây | 2.5 | Điểm tối thiểu cho view time hợp lệ |
| 5-90 giây | 2.5 - 4.0 | Tính tỉ lệ tuyến tính |
| ≥ 90 giây | 4.0 | Điểm tối đa cho view time |

**Quy tắc cập nhật:**
- Lần xem đầu tiên: Tạo rating mới với điểm từ view time
- Lần xem sau: Chỉ cập nhật nếu điểm mới cao hơn điểm hiện tại

**Công thức tính:**
```
score = 2.5 + ((view_time - 5) / (90 - 5)) * (4.0 - 2.5)
```

**Ví dụ:**
- 5 giây → 2.5 điểm
- 30 giây → 2.94 điểm
- 60 giây → 3.47 điểm
- 90 giây → 4.0 điểm

### 2. Like

**Quy tắc:** +4 điểm vào điểm hiện tại

**Ví dụ:**
- Điểm hiện tại: 2.5 → Sau khi Like: 5.0 (max)
- Điểm hiện tại: 0.8 → Sau khi Like: 4.8
- Điểm hiện tại: 3.0 → Sau khi Like: 5.0 (capped tại max)

### 3. Dislike

**Quy tắc:** -5 điểm vào điểm hiện tại HOẶC điểm tối thiểu = 1.0

**Ví dụ:**
- Điểm hiện tại: 4.0 → Sau khi Dislike: 1.0 (min)
- Điểm hiện tại: 2.0 → Sau khi Dislike: 1.0 (min)
- Điểm hiện tại: 3.5 → Sau khi Dislike: 1.0 (min)

### 4. Comment

**Quy tắc:** +0.5 điểm (chỉ tính lần đầu tiên)

**Ví dụ:**
- Comment lần 1: +0.5 điểm
- Comment lần 2, 3, 4...: Không cộng thêm

## Giới hạn điểm số

- **Điểm tối thiểu:** 1.0
- **Điểm tối đa:** 5.0
- Mọi điểm số được làm tròn đến 2 chữ số thập phân

## Kịch bản sử dụng

### Kịch bản 1: User mới xem place

1. User xem place trong 60 giây → **3.47 điểm**
2. User để lại comment → **3.47 + 0.5 = 3.97 điểm**
3. User bấm like → **3.97 + 4 = 5.0 điểm** (max)

### Kịch bản 2: User không thích

1. User xem place 10 giây → **2.59 điểm**
2. User bấm dislike → **2.59 - 5 = 1.0 điểm** (min)

### Kịch bản 3: User đã có rating cũ

1. Rating cũ: **3.0 điểm**
2. User xem lại 90 giây → **4.0 điểm** (cao hơn, cập nhật)
3. User comment → **4.0 + 0.5 = 4.5 điểm**
4. User like → **4.5 + 4 = 5.0 điểm** (max)

### Kịch bản 4: User thay đổi ý kiến

1. User xem 60 giây → **3.47 điểm**
2. User like → **3.47 + 4 = 5.0 điểm**
3. User đổi sang dislike → **5.0 - 5 = 1.0 điểm** (min)

## API Endpoints

### 1. Track View Time

**Endpoint:** `POST /rating/view-time`

**Body:**
```json
{
  "place_id": 123,
  "view_time_seconds": 60.5
}
```

**Response:**
```json
{
  "user_id": 1,
  "place_id": 123,
  "score": 2.59,
  "status": "created"
}
```

### 2. Like/Dislike Place

**Endpoint:** `POST /likes/place`

**Body:**
```json
{
  "place_id": 123,
  "is_like": true
}
```

**Response:**
```json
{
  "action": "created",
  "status": "liked",
  "data": {
    "id": 1,
    "user_id": 1,
    "place_id": 123,
    "created_at": "2025-12-16T10:30:00"
  }
}
```

**Note:** Rating score tự động được cập nhật khi like/dislike

### 3. Create Comment

**Endpoint:** `POST /comments`

**Body:**
```json
{
  "place_id": 123,
  "content": "Great place!"
}
```

**Response:**
```json
{
  "id": 1,
  "user_id": 1,
  "username": "john",
  "place_id": 123,
  "content": "Great place!",
  "created_at": "2025-12-16T10:30:00"
}
```

**Note:** Rating score tự động +0.5 cho comment đầu tiên

### 4. Get User Rating

**Endpoint:** `GET /rating/rating/{place_id}`

**Response:**
```json
{
  "place_id": 123,
  "score": 4.5,
  "user_id": 1
}
```

## Implementation Files

### 1. `scoring_service.py`

Chứa class `RatingScorer` với các method:

- `calculate_view_time_score()`: Tính điểm từ thời gian xem
- `calculate_rating_score()`: Tính tổng điểm từ tất cả interactions
- `update_rating()`: Cập nhật hoặc tạo rating mới trong database

### 2. `routers/rating.py`

- `POST /rating/view-time`: Track thời gian xem
- `GET /rating/rating/{place_id}`: Lấy rating của user

### 3. `routers/like.py`

- `POST /likes/place`: Like/Dislike với tự động cập nhật rating

### 4. `routers/comment.py`

- `POST /comments`: Tạo comment với tự động cập nhật rating

## Database Schema

### Rating Table

```sql
CREATE TABLE rating (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    place_id INTEGER NOT NULL,
    score FLOAT NOT NULL,
    FOREIGN KEY(user_id) REFERENCES user(id),
    FOREIGN KEY(place_id) REFERENCES place(id)
);
```

## Testing

Chạy demo để xem thuật toán hoạt động:

```bash
cd backend
python test_rating_algorithm.py
```

## Notes

1. **View time cập nhật thông minh:** 
   - Lần xem đầu tiên: Tạo rating mới
   - Lần xem sau: Chỉ cập nhật nếu điểm cao hơn điểm hiện tại

2. **Comment bonus chỉ tính 1 lần:** Chỉ comment đầu tiên được cộng +0.5 điểm.

3. **Điểm số luôn trong khoảng [1.0, 5.0]:** Tất cả tính toán đều được clamp trong giới hạn này.

4. **Like/Dislike có thể thay đổi:** User có thể đổi từ like sang dislike và ngược lại, điểm số sẽ được tính toán lại.

5. **Bấm nhầm được loại bỏ:** View time < 5 giây không được tính để tránh trường hợp bấm nhầm.

6. **Thời gian xem tối đa 90 giây:** View time > 90 giây được capped ở mức 4.0 điểm.
