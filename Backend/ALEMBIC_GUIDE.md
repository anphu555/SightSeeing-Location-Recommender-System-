# Hướng dẫn sử dụng Alembic cho Database Migration

## Giới thiệu

Alembic đã được cấu hình và sẵn sàng sử dụng để quản lý các thay đổi database trong dự án này.

## Cách sử dụng nhanh

### 1. Tạo migration mới khi có thay đổi model

Khi bạn thay đổi bất kỳ model nào trong `app/schemas.py` (thêm field, xóa field, thay đổi kiểu dữ liệu, v.v.), chạy lệnh:

```bash
migrate.bat create "Mô tả thay đổi của bạn"
```

Ví dụ:
```bash
migrate.bat create "Add email field to User table"
migrate.bat create "Add rating column to Place"
```

### 2. Áp dụng migration vào database

Sau khi tạo migration, áp dụng nó vào database:

```bash
migrate.bat upgrade
```

### 3. Rollback migration (nếu cần)

Nếu cần hoàn tác migration cuối cùng:

```bash
migrate.bat downgrade
```

### 4. Xem trạng thái migration hiện tại

```bash
migrate.bat current
```

### 5. Xem lịch sử migration

```bash
migrate.bat history
```

## Cách sử dụng chi tiết với lệnh Python

Nếu bạn muốn chạy trực tiếp bằng Python:

### Tạo migration mới
```bash
python -m alembic revision --autogenerate -m "Mô tả thay đổi"
```

### Áp dụng tất cả migrations
```bash
python -m alembic upgrade head
```

### Rollback một migration
```bash
python -m alembic downgrade -1
```

### Xem revision hiện tại
```bash
python -m alembic current
```

### Xem lịch sử
```bash
python -m alembic history --verbose
```

### Rollback về một revision cụ thể
```bash
python -m alembic downgrade <revision_id>
```

## Workflow thông thường

1. **Sửa model** trong `app/schemas.py`:
   ```python
   class User(SQLModel, table=True):
       id: Optional[int] = Field(default=None, primary_key=True)
       username: str = Field(index=True, unique=True)
       hashed_password: str
       email: Optional[str] = None  # ← Field mới
   ```

2. **Tạo migration**:
   ```bash
   migrate.bat create "Add email to User"
   ```

3. **Kiểm tra file migration** được tạo trong `alembic/versions/`

4. **Áp dụng migration**:
   ```bash
   migrate.bat upgrade
   ```

5. **Kiểm tra** xem database đã được cập nhật chưa

## Lưu ý quan trọng

- ✅ **LUÔN** review file migration trước khi apply
- ✅ **LUÔN** backup database trước khi chạy migration trên production
- ✅ **LUÔN** test migration trên development environment trước
- ❌ **KHÔNG** chỉnh sửa trực tiếp database mà không qua Alembic
- ❌ **KHÔNG** xóa file migration đã được apply

## Cấu hình hiện tại

- Database: `vietnamtravel.db` (SQLite)
- Models được theo dõi: `User`, `Place`, `Rating`
- Migration directory: `alembic/versions/`

## Troubleshooting

### Alembic không phát hiện thay đổi?

Đảm bảo model của bạn:
1. Có `table=True` trong khai báo
2. Được import trong `alembic/env.py`
3. Kế thừa từ `SQLModel`

### Lỗi khi chạy migration?

1. Kiểm tra xem database file có bị lock không
2. Đảm bảo không có process nào đang sử dụng database
3. Kiểm tra log trong console để biết chi tiết lỗi

### Cần rollback nhiều migrations?

```bash
python -m alembic downgrade <revision_id>
```

Hoặc rollback tất cả:
```bash
python -m alembic downgrade base
```
