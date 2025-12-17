# 🚀 HƯỚNG DẪN CHẠY EVALUATION VỚI WSL + VENV

## ✅ Quick Start (WSL)

### 1. Mở WSL Terminal

```bash
# Di chuyển đến thư mục backend
cd /mnt/d/SightSeeing-Location-Recommender-System-/backend
```

### 2. Cấp quyền thực thi cho scripts

```bash
chmod +x *.sh
```

### 3. Chạy scripts

#### Option A: Quick Demo (Kiểm tra nhanh)
```bash
./run_quick_demo.sh
```

#### Option B: Tạo Test Data
```bash
./run_create_test_data.sh
```

#### Option C: Full Evaluation
```bash
./run_evaluation.sh
```

#### Option D: Chạy tất cả (Interactive)
```bash
./run_demo.sh
```

---

## 📋 Manual Commands (nếu muốn chạy từng bước)

```bash
# Activate venv
source ../.venv/bin/activate

# Kiểm tra venv
which python
# Should show: .../SightSeeing-Location-Recommender-System-/.venv/bin/python

# Chạy quick demo
python quick_demo.py

# Tạo test data
python create_test_data.py

# Chạy full evaluation
python evaluate_recsys.py

# Deactivate venv (khi xong)
deactivate
```

---

## 🔍 Xem Kết Quả

```bash
# Xem kết quả JSON
cat evaluation_results.json | jq

# Hoặc dùng Python để xem đẹp hơn
python -c "import json; print(json.dumps(json.load(open('evaluation_results.json')), indent=2))"

# Xem detailed results
head -20 evaluation_detailed.csv
```

---

## 📊 Scripts Có Sẵn

| Script | Mô tả |
|--------|-------|
| `run_quick_demo.sh` | Chạy demo nhanh, kiểm tra data quality |
| `run_create_test_data.sh` | Tạo 8 test users với synthetic data |
| `run_evaluation.sh` | Chạy full evaluation với metrics |
| `run_demo.sh` | Chạy tất cả bước (interactive) |

---

## ⚡ One-liner Commands

```bash
# Quick test
cd /mnt/d/SightSeeing-Location-Recommender-System-/backend && source ../.venv/bin/activate && python quick_demo.py

# Create test data
cd /mnt/d/SightSeeing-Location-Recommender-System-/backend && source ../.venv/bin/activate && python create_test_data.py

# Run evaluation
cd /mnt/d/SightSeeing-Location-Recommender-System-/backend && source ../.venv/bin/activate && python evaluate_recsys.py
```

---

## 🐛 Troubleshooting

### Lỗi: Permission denied
```bash
chmod +x *.sh
```

### Lỗi: venv not found
```bash
# Kiểm tra venv tồn tại
ls -la ../.venv/bin/activate

# Nếu không có, tạo mới
cd /mnt/d/SightSeeing-Location-Recommender-System-
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
```

### Lỗi: Module not found
```bash
# Activate venv và cài packages
source ../.venv/bin/activate
pip install pandas numpy scikit-learn
```

### Kiểm tra Python đang dùng
```bash
source ../.venv/bin/activate
which python
python --version
pip list | grep -E "pandas|numpy|scikit"
```

---

## 📁 Output Files

Sau khi chạy evaluation, bạn sẽ có:

```
backend/
├── evaluation_results.json      # Tổng hợp metrics
├── evaluation_detailed.csv      # Chi tiết từng user
└── (các script .py và .sh)
```

---

## 💡 Tips

1. **Luôn activate venv trước khi chạy**
   ```bash
   source ../.venv/bin/activate
   ```

2. **Check data trước khi evaluate**
   ```bash
   python quick_demo.py  # Xem có đủ data không
   ```

3. **Tạo test data nếu thiếu**
   ```bash
   python create_test_data.py  # Tạo synthetic data
   ```

4. **Xem kết quả ngay trong terminal**
   ```bash
   python evaluate_recsys.py  # In kết quả ra console
   ```

---

**Happy evaluating! 🎯**
