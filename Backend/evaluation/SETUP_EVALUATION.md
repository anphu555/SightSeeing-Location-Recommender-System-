# 🔧 SETUP HƯỚNG DẪN

## ⚠️ LỖI: Thiếu Dependencies

Script đánh giá cần các thư viện sau:
- pandas
- numpy  
- scikit-learn

## ✅ CÁCH KHẮC PHỤC

### Cách 1: Cài đặt tất cả dependencies (Khuyên dùng)

```bash
cd backend
pip install -r requirements.txt
```

### Cách 2: Chỉ cài packages cần thiết

```bash
pip install pandas numpy scikit-learn
```

### Cách 3: Dùng script install tự động

```bash
cd backend
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## 🔍 SAU KHI CÀI ĐẶT

Kiểm tra lại:

```bash
python check_setup.py
```

Nếu thấy "✅ Tất cả dependencies đã được cài đặt!" thì đã OK!

## 📝 CHẠY EVALUATION

```bash
# Bước 1: Demo nhanh
python quick_demo.py

# Bước 2: Tạo test data (nếu cần)
python create_test_data.py

# Bước 3: Full evaluation
python evaluate_recsys.py
```

## ❓ Nếu vẫn gặp lỗi

### Windows:
```bash
py -m pip install pandas numpy scikit-learn
```

### Linux/Mac:
```bash
python3 -m pip install pandas numpy scikit-learn
```

### Virtual Environment:
```bash
# Tạo venv
python -m venv venv

# Activate
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install
pip install -r requirements.txt
```

---

**Sau khi cài đặt xong, chạy lại `python quick_demo.py`** 🚀
