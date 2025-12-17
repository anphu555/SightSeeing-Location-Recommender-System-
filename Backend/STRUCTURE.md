# 📂 BACKEND STRUCTURE - Cấu trúc thư mục Backend

## 🗂️ Cấu trúc chính

```
backend/
├── 📁 app/                     # Main application code
│   ├── __init__.py
│   ├── main.py                 # FastAPI entry point
│   ├── database.py             # Database connection
│   ├── schemas.py              # SQLModel schemas
│   ├── security.py             # Authentication
│   ├── config.py               # Configuration
│   ├── 📁 routers/             # API endpoints
│   │   ├── recsysmodel.py     # Recommendation system
│   │   └── ...
│   └── 📁 services/            # Business logic
│
├── 📁 evaluation/              # ⭐ Evaluation tools & results
│   ├── README.md               # Hướng dẫn evaluation
│   ├── evaluate_recsys.py      # Main evaluation script
│   ├── analyze_*.py            # Analysis tools
│   ├── EVALUATION_*.md         # Documentation
│   └── evaluation_*.csv/json   # Results
│
├── 📁 alembic/                 # Database migrations
├── 📁 uploads/                 # User uploads (avatars, covers)
│
├── vietnamtravel.db            # Main database
├── requirements.txt            # Python dependencies
├── Dockerfile                  # Docker config
│
└── 📄 Scripts:
    ├── create_test_data.py             # Tạo dữ liệu test
    ├── create_improved_test_data.py    # Tạo dữ liệu test cải thiện
    ├── check_*.py                      # Checking scripts
    ├── cleanup_*.py                    # Cleanup scripts
    └── ...
```

## 🎯 Các thư mục quan trọng

### 📁 app/ - Application Code
Chứa toàn bộ code của ứng dụng:
- **main.py**: Entry point, khởi tạo FastAPI
- **database.py**: Database connection & session
- **schemas.py**: Database models (User, Place, Rating, etc.)
- **routers/**: API endpoints theo từng module
- **services/**: Business logic, algorithms

### 📁 evaluation/ - Evaluation Tools ⭐
**Thư mục mới được tổ chức lại!**

Chứa tất cả công cụ đánh giá hệ thống:
- Scripts evaluation
- Analysis tools
- Documentation
- Results & reports

👉 Xem [evaluation/README.md](./evaluation/README.md) để biết thêm chi tiết

### 📁 alembic/ - Database Migrations
Quản lý database schema changes:
- Migration scripts
- Version control cho database

### 📁 uploads/ - User Uploads
Lưu trữ files upload từ users:
- avatars/: Avatar images
- covers/: Cover images

## 🚀 Scripts thường dùng

### Development
```bash
# Chạy server
python -m uvicorn app.main:app --reload

# Check setup
python check_setup.py

# Check database
python check_data.py
```

### Testing & Data
```bash
# Tạo test data
python create_test_data.py

# Tạo test data cải thiện
python create_improved_test_data.py

# Cleanup test users
python cleanup_test_users.py
```

### Evaluation (trong evaluation/)
```bash
cd evaluation/

# Chạy evaluation
python evaluate_recsys.py

# Phân tích methodology
python analyze_evaluation_methodology.py

# Phân tích category consistency
python analyze_rating_categories.py
```

## 📝 Documents quan trọng

| File | Mô tả |
|------|-------|
| [evaluation/README.md](./evaluation/README.md) | Hướng dẫn đầy đủ về evaluation |
| [evaluation/EVALUATION_EXPLAINED.md](./evaluation/EVALUATION_EXPLAINED.md) | Giải thích phương pháp evaluation |
| ALGORITHM_FLOW.md | Luồng hoạt động của thuật toán |
| RATING_ALGORITHM.md | Chi tiết thuật toán rating |
| QUICK_REFERENCE.txt | Quick commands reference |

## 🔍 Tìm file nhanh

### Cần làm gì với Evaluation?
→ Vào [evaluation/](./evaluation/) và đọc README.md

### Cần hiểu thuật toán?
→ Đọc ALGORITHM_FLOW.md và RATING_ALGORITHM.md

### Cần setup database?
→ Xem ALEMBIC_GUIDE.md

### Cần API documentation?
→ Chạy server và vào http://localhost:8000/docs

## 💡 Tips

1. **Evaluation**: Tất cả files liên quan đến evaluation giờ nằm trong `evaluation/`
2. **Data**: Test data scripts vẫn ở root (backend/) để dễ chạy
3. **Imports**: Scripts trong `evaluation/` đã được update imports để hoạt động đúng
4. **Documentation**: Mỗi thư mục có README.md riêng

---

**Cập nhật:** December 17, 2025
**Cấu trúc mới:** Evaluation được tách riêng để dễ quản lý
