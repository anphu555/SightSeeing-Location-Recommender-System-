# GIẢI THÍCH PHƯƠNG PHÁP EVALUATION

## ❓ CÂU HỎI CỦA BẠN
> "Làm sao biết được precision bao nhiêu khi chỉ có user và rating, không biết user thích gì?"

## 💡 GIẢI ĐÁP NGẮN GỌN

**Ground Truth = Test Set (những địa điểm user đã rate cao nhưng bị GIẤU ĐI)**

### Quy trình:

```
User A có 10 địa điểm đã rate cao (score >= 3.0)
│
├─ CHIA DỮ LIỆU (Train/Test Split 80/20)
│  ├─ Train: 8 địa điểm → Model học từ đây
│  └─ Test: 2 địa điểm → GIẤU ĐI (ground truth)
│
├─ MODEL HỌC
│  └─ Model chỉ biết 8 địa điểm, KHÔNG biết 2 địa điểm test
│
├─ MODEL DỰ ĐOÁN
│  └─ Recommend top-5: [P1, P2, P3, P4, P5]
│
└─ ĐÁNH GIÁ
   └─ So sánh top-5 với 2 địa điểm test (ground truth)
   
   Nếu trong top-5 có 1 địa điểm test:
   • Precision@5 = 1/5 = 0.2 (20% đúng)
   • Recall@5 = 1/2 = 0.5 (tìm được 50%)
```

## 📋 VÍ DỤ CỤ THỂ

### User thích biển:

**Train set (model biết):**
- Nha Trang Beach (score: 5.0) ⛱️
- My Khe Beach (score: 4.5) ⛱️
- Vung Tau Beach (score: 4.0) ⛱️

**Test set (GIẤU ĐI - ground truth):**
- Ha Long Beach (score: 4.5) ⛱️

**Model recommend top-3:**
1. Da Nang Beach ⛱️ ✓ (tương tự train)
2. Ha Long Beach ⛱️ ✓ **← TRÚNG ground truth!**
3. Phu Quoc Beach ⛱️ ✓ (tương tự train)

**Kết quả:**
- ✓ Precision@3 = 1/3 = 0.33 (có 1 item trong ground truth)
- ✓ Recall@3 = 1/1 = 1.0 (tìm được 100% ground truth)
- → Model học tốt: User thích biển → recommend biển

## 🎯 TẠI SAO HỢP LÝ?

### 1. **Giả định cơ bản:**
- Score cao (>= 3.0) = User thích địa điểm đó
- User thích A, B, C → có khả năng thích D (tương tự A, B, C)

### 2. **Test như thực tế:**
- Train = Dữ liệu quá khứ (đã biết)
- Test = Tương lai (chưa biết, cần dự đoán)
- Evaluation = Kiểm tra model có dự đoán đúng tương lai không

### 3. **Metrics đo lường:**
- **Precision@K:** Trong K recommendations, bao nhiêu % là đúng?
- **Recall@K:** Trong tất cả items user thích, tìm được bao nhiêu %?
- **NDCG@K:** Items đúng có ở vị trí cao trong ranking không?

## 📊 PHÂN TÍCH DỮ LIỆU THỰC TẾ

Chạy script để xem:
```bash
python analyze_evaluation_methodology.py
```

### Kết quả phân tích:
- ✓ 140 users đủ điều kiện cho evaluation
- ✓ Trung bình 13.9 train items, 3.0 test items
- ⚠️ Tag overlap: 58.2% (hơi thấp)
  - → Users không quá consistent trong preferences
  - → Cần cải thiện data với `create_improved_test_data.py`

## 🔍 PHÂN TÍCH CATEGORY CONSISTENCY

Để kiểm tra xem user có rate đúng thể loại không:
```bash
python analyze_rating_categories.py
```

### Kết quả:
- Users hiện tại: 0% specialized (rate rất đa dạng)
- → Giải thích: Tags như "sightseeing", "historical" xuất hiện ở hầu hết places
- → Khó phân biệt preferences rõ ràng

### Cải thiện:
```bash
python create_improved_test_data.py
```
- Tạo users với preferences rõ ràng
- Ví dụ: `beach_lover` chỉ rate địa điểm có tag beach/coastal
- → Dễ verify algorithm hoạt động đúng

## ✅ KẾT LUẬN

### Phương pháp evaluation **HỢP LÝ** vì:
1. ✓ Sử dụng Train/Test Split chuẩn ML
2. ✓ Ground truth = Items user thực sự thích (test set)
3. ✓ Metrics phù hợp (Precision, Recall, NDCG)

### Dữ liệu hiện tại:
- ⚠️ Cần cải thiện: Users không consistent
- 💡 Giải pháp: Tạo synthetic data với preferences rõ ràng

### Về việc bạn test thấy "thích biển → recommend biển":
- ✓ **Đúng:** Algorithm hoạt động tốt!
- Nếu bạn rate nhiều địa điểm biển (score cao)
- → Model học pattern: user này thích biển
- → Recommend các địa điểm biển khác
- → Đó là kết quả mong muốn! 🎉

## 📝 TÓM LẠI NGẮN GỌN

| Khái niệm | Giải thích |
|-----------|------------|
| **Ground Truth** | Địa điểm user thực sự thích (score cao) nhưng bị giấu đi trong test set |
| **Train Set** | Model học từ đây (80% data) |
| **Test Set** | Dùng để đánh giá (20% data), model KHÔNG biết khi training |
| **Precision** | % recommendations đúng |
| **Recall** | % ground truth items được tìm thấy |
| **Evaluation** | So sánh recommendations với test set |

---

**Tài liệu liên quan:**
- [evaluate_recsys.py](./evaluate_recsys.py) - Code evaluation
- [analyze_evaluation_methodology.py](./analyze_evaluation_methodology.py) - Phân tích chi tiết
- [analyze_rating_categories.py](./analyze_rating_categories.py) - Phân tích category consistency
