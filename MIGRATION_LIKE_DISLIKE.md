# Migration Guide: Like/Dislike System Update

## Tổng Quan

Hệ thống đã được cập nhật từ **Like/Unlike** (bỏ like) sang **Like/Dislike** (thích/không thích) giống YouTube.

## Thay Đổi

### 1. Database Schema

**Bảng `Like`** đã thêm cột mới:
- `is_like`: Boolean (True = Like, False = Dislike)

### 2. Logic Tương Tác

**Trạng thái:**
- **Neutral** (không vote): Cả 2 nút đều chưa được chọn
- **Liked**: Nút thumbs-up được chọn (màu teal #14838B)
- **Disliked**: Nút thumbs-down được chọn (màu đỏ #e74c3c)

**Hành vi:**
- Bấm Like khi đang neutral → Like được chọn
- Bấm Like khi đang liked → Bỏ like (về neutral)
- Bấm Like khi đang disliked → Chuyển sang liked (bỏ dislike)
- Bấm Dislike tương tự ngược lại

### 3. API Changes

#### API Endpoint Mới (Recommended)

**POST /api/v1/likes/place**
```json
{
  "place_id": 123,
  "is_like": true  // true = like, false = dislike
}
```

**Response:**
- Nếu tạo mới hoặc update: Trả về LikeResponse
- Nếu toggle off (bỏ vote): `{"message": "Removed successfully"}`

**POST /api/v1/likes/comment**
```json
{
  "comment_id": 456,
  "is_like": true
}
```

#### API Check Status

**GET /api/v1/likes/check/place/{place_id}**

**Response:**
```json
{
  "liked": true,      // true nếu đang liked
  "disliked": false,  // true nếu đang disliked
  "status": "liked"   // "liked" | "disliked" | "neutral"
}
```

#### API Deprecated (vẫn hoạt động để backward compatibility)

- `DELETE /api/v1/likes/place/{place_id}` - Dùng POST với same is_like để toggle
- `DELETE /api/v1/likes/comment/{comment_id}` - Dùng POST với same is_like để toggle

### 4. Frontend Changes

#### detail.html
- `btnUnlikePlace` → `btnDislikePlace`
- Title: "Unlike this place" → "Dislike this place"

#### detail.js
Các hàm đã được cập nhật:
- `setupPlaceLikeButtons()` - Hỗ trợ like/dislike
- `togglePlaceLike()` - Logic toggle mới
- `updatePlaceLikeUI()` - Nhận status: 'liked'|'disliked'|'neutral'
- `setupCommentLikeButtons()` - Comment like/dislike
- `toggleCommentLike()` - Comment toggle logic
- `updateCommentLikeUI()` - Comment UI với 3 trạng thái

#### result.js
- `togglePlaceLike()` đã được cập nhật với logic mới

#### profile.js
- **Không thay đổi** - "Unlike" trong profile có nghĩa là xóa khỏi danh sách yêu thích (remove from favorites)

## Cách Chạy Migration

### 1. Backup Database
```bash
cd backend
cp vietnamtravel.db vietnamtravel.db.backup
```

### 2. Chạy Migration
```bash
# Windows
migrate.bat

# Linux/Mac
alembic upgrade head
```

### 3. Restart Backend
```bash
# Stop backend nếu đang chạy
# Start lại backend
```

## Testing

### Test Cases

1. **Like Place**
   - Bấm like → Nút like active (màu teal)
   - Bấm like lại → Về neutral
   
2. **Dislike Place**
   - Bấm dislike → Nút dislike active (màu đỏ)
   - Bấm dislike lại → Về neutral

3. **Switch Like ↔ Dislike**
   - Đang liked → Bấm dislike → Chuyển sang disliked
   - Đang disliked → Bấm like → Chuyển sang liked

4. **Comment Like/Dislike**
   - Test tương tự với comment

5. **Auth Flow**
   - Khi chưa login → Hiện toast yêu cầu login
   - Sau khi login → Like/dislike hoạt động bình thường

## Rollback

Nếu cần rollback:

```bash
cd backend
alembic downgrade -1
```

Sau đó restore code cũ từ git history.

## Notes

- Migration tự động set `is_like = True` cho tất cả like cũ
- API cũ (DELETE) vẫn hoạt động để không ảnh hưởng đến code cũ
- UI tự động phát hiện trạng thái và hiển thị đúng
- Profile page giữ nguyên logic "Unlike" = remove from favorites

## Support

Nếu gặp vấn đề, kiểm tra:
1. Database đã migrate chưa: `alembic current`
2. Backend logs có lỗi không
3. Browser console có lỗi JavaScript không
4. Token authentication có hết hạn không
