# 📊 EVALUATION - Thư mục Đánh giá Hệ thống

Thư mục này chứa tất cả các công cụ và tài liệu liên quan đến việc đánh giá (evaluation) hệ thống recommendation.

## 📁 Cấu trúc

### 🔧 Scripts chính

| File | Mô tả |
|------|-------|
| **evaluate_recsys.py** | Script chính để chạy evaluation, tính toán metrics (Precision, Recall, NDCG, MAP) |
| **analyze_evaluation_methodology.py** | Phân tích và giải thích phương pháp evaluation (Train/Test split, Ground truth) |
| **analyze_rating_categories.py** | Phân tích category consistency - kiểm tra user có rate đúng thể loại không |

### 📄 Tài liệu

| File | Mô tả |
|------|-------|
| **EVALUATION_EXPLAINED.md** | ⭐ Giải thích chi tiết phương pháp evaluation (bắt đầu từ đây!) |
| **EVALUATION_GUIDE.md** | Hướng dẫn chi tiết cách chạy evaluation |
| **EVALUATION_REPORT.md** | Báo cáo kết quả evaluation |
| **SETUP_EVALUATION.md** | Hướng dẫn setup môi trường evaluation |

### 📊 Kết quả

| File | Mô tả |
|------|-------|
| **evaluation_detailed.csv** | Kết quả chi tiết cho từng user |
| **evaluation_results.json** | Tổng hợp kết quả metrics |
| **evaluation_output.txt** | Output logs của quá trình evaluation |

### 🚀 Scripts chạy

| File | Mô tả |
|------|-------|
| **run_evaluation.bat** | Chạy evaluation trên Windows (CMD) |
| **run_evaluation.sh** | Chạy evaluation trên Linux/Mac |
| **run_full_evaluation.sh** | Chạy full evaluation với tất cả tests |
| **Run-Evaluation.ps1** | Chạy evaluation trên Windows (PowerShell) |

## 🚀 Cách sử dụng nhanh

### 1. Hiểu phương pháp evaluation

```bash
# Đọc document giải thích
cat EVALUATION_EXPLAINED.md

# Hoặc chạy phân tích
python analyze_evaluation_methodology.py
```

### 2. Phân tích data hiện tại

```bash
# Kiểm tra category consistency
python analyze_rating_categories.py
```

### 3. Chạy evaluation

```bash
# Windows PowerShell
.\Run-Evaluation.ps1

# Windows CMD
.\run_evaluation.bat

# Linux/Mac
./run_evaluation.sh
```

### 4. Xem kết quả

```bash
# Xem kết quả tổng quan
cat evaluation_output.txt

# Xem chi tiết từng user
cat evaluation_detailed.csv
```

## 📋 Quy trình Evaluation

```
1. Chuẩn bị dữ liệu
   └─ Tạo test data với ../create_test_data.py

2. Chia Train/Test (80/20)
   └─ Train: Model học từ đây
   └─ Test: Giấu đi, dùng để đánh giá (Ground Truth)

3. Model dự đoán
   └─ Recommend top-K items cho mỗi user

4. So sánh với Ground Truth
   └─ Tính Precision@K, Recall@K, NDCG@K, MAP

5. Xuất kết quả
   └─ evaluation_detailed.csv
   └─ evaluation_results.json
   └─ evaluation_output.txt
```

## 📊 Metrics được đo

| Metric | Ý nghĩa | Giá trị tốt |
|--------|---------|-------------|
| **Precision@K** | % recommendations đúng trong top-K | Cao hơn tốt (0-1) |
| **Recall@K** | % relevant items được tìm thấy | Cao hơn tốt (0-1) |
| **F1@K** | Harmonic mean của Precision & Recall | Cao hơn tốt (0-1) |
| **NDCG@K** | Đánh giá ranking quality | Cao hơn tốt (0-1) |
| **MAP** | Mean Average Precision | Cao hơn tốt (0-1) |
| **Coverage** | % items được recommend | 0.3-0.5 là tốt |
| **Diversity** | Độ đa dạng recommendations | 0.5-0.8 là tốt |

## 🎯 Kết quả hiện tại

Xem chi tiết trong [EVALUATION_REPORT.md](./EVALUATION_REPORT.md)

**Tóm tắt:**
- Precision@5: ~0.26
- Recall@5: ~0.27
- NDCG@5: ~0.32
- MAP: ~0.19

→ Algorithm hoạt động tốt, có thể cải thiện thêm bằng cách tăng dữ liệu training

## 💡 FAQs

### ❓ Ground truth là gì?
→ Xem [EVALUATION_EXPLAINED.md](./EVALUATION_EXPLAINED.md) section "GIẢI ĐÁP NGẮN GỌN"

### ❓ Làm sao biết precision khi chỉ có ratings?
→ Sử dụng Train/Test split - giấu một phần ratings làm ground truth

### ❓ User rate đúng thể loại không?
→ Chạy `python analyze_rating_categories.py` để kiểm tra

### ❓ Cải thiện kết quả evaluation như thế nào?
→ Tạo dữ liệu test tốt hơn với `../create_improved_test_data.py`

## 🔗 Liên kết

- [Quay về Backend](../)
- [Tạo test data](../create_test_data.py)
- [Recommendation System](../app/routers/recsysmodel.py)

---

**Cập nhật:** December 17, 2025
**Tác giả:** Evaluation Team
