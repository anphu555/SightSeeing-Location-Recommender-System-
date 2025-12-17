# 📊 HƯỚNG DẪN ĐÁNH GIÁ RECOMMENDATION SYSTEM

## Tổng quan

Bộ công cụ đánh giá (evaluation framework) này giúp bạn:
- ✅ Đánh giá độ chính xác của thuật toán đề xuất
- ✅ Tạo test data nếu dữ liệu thực tế chưa đủ
- ✅ Hiểu rõ điểm mạnh/yếu của hệ thống
- ✅ So sánh các thuật toán khác nhau

---

## 🚀 Quick Start

### Bước 1: Demo nhanh (kiểm tra hệ thống)

```bash
cd backend
python quick_demo.py
```

Script này sẽ:
- Kiểm tra chất lượng dữ liệu hiện có
- Chạy một vài scenarios demo
- Đề xuất next steps

### Bước 2: Tạo test data (nếu cần)

Nếu dữ liệu thực tế chưa đủ (< 50 interactions):

```bash
python create_test_data.py
```

Script này tạo:
- 8 test users với profiles khác nhau
- 100+ interactions (ratings + likes)
- Dữ liệu phản ánh đúng preferences của users

### Bước 3: Chạy full evaluation

```bash
python evaluate_recsys.py
```

Script này sẽ:
- Tạo train/test split (80/20)
- Đánh giá với nhiều metrics
- Lưu kết quả vào files

### Bước 4: Xem kết quả

Kết quả được lưu ở:
- `evaluation_results.json` - Tổng hợp metrics
- `evaluation_detailed.csv` - Chi tiết từng user

---

## 📈 Các Metrics Đánh Giá

### 1. **Precision@K**
- **Ý nghĩa**: Tỉ lệ items được đề xuất là relevant (user thích)
- **Công thức**: `(# relevant in top-K) / K`
- **Ví dụ**: Precision@10 = 0.3 → 30% trong 10 items đề xuất là user thích
- **Tốt khi**: ≥ 0.2 (20%)

### 2. **Recall@K**
- **Ý nghĩa**: Tỉ lệ items relevant được tìm thấy trong top-K
- **Công thức**: `(# relevant in top-K) / (total relevant)`
- **Ví dụ**: User thích 20 places, tìm được 5 trong top-10 → Recall@10 = 25%
- **Tốt khi**: ≥ 0.15 (15%)

### 3. **F1@K**
- **Ý nghĩa**: Harmonic mean của Precision và Recall
- **Công thức**: `2 * (Precision * Recall) / (Precision + Recall)`
- **Tốt khi**: ≥ 0.15

### 4. **NDCG@K** (Normalized Discounted Cumulative Gain)
- **Ý nghĩa**: Đánh giá ranking quality (items relevant ở vị trí cao = tốt)
- **Tốt khi**: ≥ 0.3 (30%)
- **Xuất sắc khi**: ≥ 0.5 (50%)

### 5. **MAP** (Mean Average Precision)
- **Ý nghĩa**: Trung bình precision tại mỗi relevant item
- **Tốt khi**: ≥ 0.2 (20%)

### 6. **Coverage**
- **Ý nghĩa**: Tỉ lệ items trong catalog được đề xuất ít nhất 1 lần
- **Tốt khi**: ≥ 0.3 (30% catalog)
- **Ý nghĩa**: Hệ thống không bị "filter bubble", đề xuất đa dạng

### 7. **Diversity**
- **Ý nghĩa**: Độ đa dạng của recommendations
- **Tốt khi**: ≥ 0.5

---

## 🎯 Tiêu Chí Đánh Giá

| Chất lượng | Precision@10 | NDCG@10 | MAP | Nhận xét |
|-----------|--------------|---------|-----|----------|
| 🌟 **XUẤT SẮC** | ≥ 30% | ≥ 40% | ≥ 30% | Production-ready |
| ✅ **TỐT** | ≥ 20% | ≥ 30% | ≥ 20% | Chấp nhận được |
| ⚠️ **TRUNG BÌNH** | ≥ 10% | ≥ 20% | ≥ 10% | Cần cải thiện |
| ❌ **YẾU** | < 10% | < 20% | < 10% | Cần làm lại |

---

## 🔍 Ví Dụ Kết Quả

### Kết quả tốt:
```
📊 Số users được đánh giá: 8
📊 Trung bình relevant items/user: 10.5

📈 PRECISION (Độ chính xác của đề xuất):
   • Precision@5: 28.50%
   • Precision@10: 24.25%
   • Precision@20: 18.12%

📈 RECALL (Tỉ lệ items relevant được tìm thấy):
   • Recall@5: 13.57%
   • Recall@10: 23.10%
   • Recall@20: 34.50%

📈 NDCG (Ranking Quality):
   • NDCG@5: 31.20%
   • NDCG@10: 35.80%
   • NDCG@20: 38.50%

📈 MAP: 26.40%
📈 COVERAGE: 42.30%
📈 DIVERSITY: 68.50%

Kết luận: ✅ TỐT
```

**Giải thích:**
- ✅ Precision@10 = 24% → Cứ 10 items đề xuất thì có ~2-3 items user thích
- ✅ NDCG@10 = 36% → Ranking khá tốt, items relevant thường ở vị trí cao
- ✅ Coverage = 42% → Đề xuất đa dạng, không bị filter bubble

---

## 🛠️ Cải Thiện Thuật Toán

### Nếu kết quả yếu (< 10%):

#### 1. **Cải thiện Data Quality**
```python
# Kiểm tra dữ liệu
python quick_demo.py

# Cần:
# - Ít nhất 50+ interactions (ratings/likes)
# - Ít nhất 5+ active users
# - Interactions phản ánh đúng preferences
```

#### 2. **Feature Engineering**
- Cải thiện tags của places (rõ ràng, nhất quán)
- Thêm descriptions chi tiết
- Thêm metadata (location, price, type...)

#### 3. **Thử thuật toán khác**
```python
# Content-based (hiện tại) vs Collaborative Filtering
# Hybrid approach (kết hợp cả 2)
```

#### 4. **Tune Hyperparameters**
```python
# Trong recsysmodel.py, thử điều chỉnh:

# 1. Trọng số hybrid
final_vec = (query_vec * 0.7) + (user_profile_vec * 0.3)
#            ^ Thử 0.6/0.4 hoặc 0.8/0.2

# 2. Vectorizer parameters
vectorizer = CountVectorizer(
    stop_words='english',
    max_features=5000  # Thử 3000, 10000
)

# 3. Boost strategies
results['score'] = results['score'] * boost_factor
```

---

## 📁 Cấu Trúc Files

```
backend/
├── evaluate_recsys.py          # 🔍 Script đánh giá chính
├── create_test_data.py         # 🎲 Tạo synthetic test data
├── quick_demo.py               # 🚀 Demo nhanh
├── EVALUATION_GUIDE.md         # 📖 File này
├── evaluation_results.json     # 📊 Kết quả tổng hợp (sau khi chạy)
└── evaluation_detailed.csv     # 📊 Kết quả chi tiết (sau khi chạy)
```

---

## 🧪 Test Scenarios

Framework hỗ trợ test nhiều scenarios:

### 1. **Cold-start Users** (users mới, không có history)
```python
# Test với tags khác nhau
recommend_two_tower(["Beach", "Nature"], user_id=None, top_k=10)
```

### 2. **Warm-start Users** (users có history)
```python
# System tự động kết hợp history + current intent
recommend_two_tower(["Mountain"], user_id=123, top_k=10)
```

### 3. **Diverse Preferences**
```python
# User thích nhiều thứ khác nhau
recommend_two_tower(["Beach", "Mountain", "Food"], user_id=456, top_k=10)
```

### 4. **No Input** (popular/diverse items)
```python
# Trang chủ, không có input
recommend_two_tower([], user_id=None, top_k=10)
```

---

## 📊 So Sánh Thuật Toán

### Để so sánh 2 thuật toán:

```python
# 1. Backup kết quả thuật toán hiện tại
# evaluation_results.json → evaluation_results_v1.json

# 2. Thay đổi thuật toán trong recsysmodel.py

# 3. Chạy lại evaluation
python evaluate_recsys.py

# 4. So sánh 2 files JSON
```

### Metrics quan trọng để so sánh:
- **Precision@10**: Độ chính xác
- **NDCG@10**: Ranking quality
- **Coverage**: Đa dạng catalog
- **MAP**: Chất lượng tổng thể

---

## ❓ FAQ

### Q: Cần bao nhiêu dữ liệu để đánh giá?
**A:** Tối thiểu:
- 5+ users với ít nhất 5 interactions/user
- 50+ total interactions
- Dùng `create_test_data.py` để tạo synthetic data

### Q: Tại sao kết quả thấp?
**A:** Có thể do:
1. Dữ liệu quá ít hoặc không chất lượng
2. Tags của places không rõ ràng
3. Thuật toán chưa phù hợp với dữ liệu
4. User preferences không được mô hình hóa tốt

### Q: NDCG khác Precision như thế nào?
**A:** 
- **Precision**: Chỉ đếm số items relevant, không quan tâm vị trí
- **NDCG**: Ưu tiên items relevant ở vị trí cao (rank 1 > rank 10)

### Q: Metrics nào quan trọng nhất?
**A:** Tùy mục tiêu:
- **E-commerce/Search**: NDCG@10 (ranking)
- **Content Discovery**: Coverage + Diversity
- **Tổng thể**: MAP (cân bằng precision + ranking)

### Q: Cold-start performance kém, làm sao?
**A:**
1. Thêm content-based filtering (đang dùng)
2. Thêm popular items fallback
3. Hỏi user preferences khi đăng ký
4. Dùng demographic info

---

## 📞 Troubleshooting

### Lỗi: "No places found in database"
```bash
# Chạy seed data
cd backend
python seed_data.py
```

### Lỗi: "Insufficient data for evaluation"
```bash
# Tạo test data
python create_test_data.py
```

### Lỗi: "Model not initialized"
```python
# Trong code, gọi:
from app.routers.recsysmodel import initialize_recsys
initialize_recsys()
```

---

## 🎓 Tham Khảo

### Papers:
- [Collaborative Filtering for Implicit Feedback Datasets](https://ieeexplore.ieee.org/document/4781121)
- [BPR: Bayesian Personalized Ranking](https://arxiv.org/abs/1205.2618)

### Metrics:
- [Information Retrieval Metrics](https://en.wikipedia.org/wiki/Evaluation_measures_(information_retrieval))
- [NDCG Explained](https://en.wikipedia.org/wiki/Discounted_cumulative_gain)

### Industry Standards:
- Netflix: NDCG@10 > 0.4
- Amazon: Precision@10 > 0.25
- Spotify: Coverage > 0.4

---

## ✅ Checklist

Trước khi đưa lên production:

- [ ] Precision@10 ≥ 20%
- [ ] NDCG@10 ≥ 30%
- [ ] Coverage ≥ 30%
- [ ] Diversity ≥ 50%
- [ ] Cold-start performance acceptable
- [ ] Response time < 200ms
- [ ] A/B testing với users thật

---

**Good luck với việc đánh giá! 🚀**
