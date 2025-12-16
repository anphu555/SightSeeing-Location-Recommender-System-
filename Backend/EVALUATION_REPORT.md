# 📊 KẾT QUẢ ĐÁNH GIÁ HỆ THỐNG ĐỀ XUẤT

**Ngày đánh giá:** December 16, 2025  
**Phương pháp:** Train/Test Split (80/20) với Leave-Out Evaluation

---

## 📈 TỔNG QUAN

- **Users được đánh giá:** 11 users
- **Interactions trong test set:** 94 (trung bình 8.5/user)
- **Tổng số địa điểm (places):** 928
- **Tags thực tế:** 290 unique tags

---

## 🎯 METRICS CHÍNH

### 1. **Precision (Độ chính xác)**
Tỉ lệ địa điểm được đề xuất mà user thực sự thích:

| K | Score | Đánh giá |
|---|-------|----------|
| @5 | **7.27%** | ⚠️ Thấp |
| @10 | **4.55%** | ⚠️ Thấp |
| @20 | **4.09%** | ⚠️ Thấp |

**Ý nghĩa:** Trong 10 địa điểm đề xuất, chỉ có ~0.5 địa điểm là user thực sự thích.

### 2. **Recall (Độ bao phủ)**
Tỉ lệ địa điểm user thích được tìm thấy trong đề xuất:

| K | Score | Đánh giá |
|---|-------|----------|
| @5 | **7.14%** | ⚠️ Thấp |
| @10 | **11.68%** | ⚠️ Thấp |
| @20 | **18.01%** | ⚠️ Trung bình |

**Ý nghĩa:** Trong 8.5 địa điểm user thích, chỉ tìm được ~1 địa điểm trong top-10.

### 3. **NDCG (Ranking Quality)**
Đánh giá chất lượng xếp hạng (items relevant ở vị trí cao hơn = tốt hơn):

| K | Score | Đánh giá |
|---|-------|----------|
| @5 | **8.02%** | ⚠️ Thấp |
| @10 | **8.65%** | ⚠️ Thấp |
| @20 | **10.68%** | ⚠️ Thấp |

**Ý nghĩa:** Ranking chưa tốt, các items relevant thường không ở vị trí cao.

### 4. **MAP (Mean Average Precision)**
Trung bình precision trên toàn bộ relevant items: **4.98%** ⚠️

### 5. **Coverage (Bao phủ catalog)**
Tỉ lệ places được đề xuất ít nhất 1 lần: **9.81%** ⚠️

**Ý nghĩa:** Chỉ 91/928 places được recommend → Có filter bubble.

### 6. **Diversity (Đa dạng)**
Độ đa dạng của recommendations: **42.72%** ✅

**Ý nghĩa:** Recommendations khá đa dạng, không lặp lại quá nhiều.

---

## 🔴 VẤN ĐỀ CHÍNH

### 1. **Precision & Recall quá thấp**
- Thuật toán hiện tại (Content-Based) không capture được preferences tốt
- Chỉ dựa vào tags matching → không đủ signal

### 2. **Coverage thấp**
- 90% places không bao giờ được recommend
- Nguyên nhân: Model chỉ recommend items có tags giống query/history

### 3. **NDCG thấp**
- Ranking chưa tốt
- Items relevant không được ưu tiên lên top

---

## 💡 NGUYÊN NHÂN

### 1. **Dữ liệu ít**
- Chỉ 11 users với đủ interactions (≥5)
- Trung bình 8.5 interactions/user → quá ít để học patterns

### 2. **Content-Based Filtering hạn chế**
```python
# Thuật toán hiện tại:
similarity = cosine_similarity(user_tags, place_tags)
```
- Chỉ dựa vào text matching
- Không học được user behavior patterns
- Cold-start users không có history → chỉ dựa vào tags đầu vào

### 3. **Tags không đủ discriminative**
- "Nature" có 464 places → quá chung chung
- "Sightseeing" có 614 places → gần như tất cả
- Tags không capture được nuances (ví dụ: romantic beach vs party beach)

---

## 🚀 GỢI Ý CẢI THIỆN

### ⭐ Ưu tiên cao

#### 1. **Chuyển sang Collaborative Filtering**
```python
# Thay vì content-based:
# user_vec = cosine_sim(user_tags, place_tags)

# Dùng collaborative filtering:
# user_vec = learned_from_user_interactions
# "Users giống tôi thích gì?"
```

**Lý do:** CF học patterns từ user behavior, không cần tags tốt.

#### 2. **Hybrid Approach**
```python
final_score = 0.6 * collaborative_score + 0.4 * content_score
```
- CF: Học từ behavior
- Content: Handle cold-start

#### 3. **Popularity Boost**
```python
# Boost popular items cho new users
if user_has_few_interactions:
    score = score * (1 + log(place_popularity))
```

### ⭐ Ưu tiên trung bình

#### 4. **Cải thiện Features**
- Thêm place descriptions vào vectorization (đã có description nhưng chưa dùng tối ưu)
- Thêm ngữ cảnh: thời gian (mùa), vị trí địa lý
- Normalize tags: "Mountain" vs "Mountains", "Ecotourism" vs "Eco-tourism"

#### 5. **Fine-tune Hyperparameters**
```python
# Trong recsysmodel.py:

# 1. Tăng trọng số user history
final_vec = (query_vec * 0.5) + (user_profile_vec * 0.5)  # Hiện tại: 0.7/0.3

# 2. Thêm TF-IDF thay vì Count
from sklearn.feature_extraction.text import TfidfVectorizer
vectorizer = TfidfVectorizer(stop_words='english', max_features=5000)

# 3. Boost liked items
if place in user_liked_places:
    score = score * 1.5
```

#### 6. **Negative Feedback**
```python
# Hiện tại chưa dùng dislike signal tốt
if user_disliked_place:
    score = score * 0.1  # Penalty mạnh hơn
```

### ⭐ Dài hạn

#### 7. **Matrix Factorization (ALS, SVD)**
```python
from sklearn.decomposition import TruncatedSVD

# User-Item matrix
# Factorize: R ≈ U × V^T
# R: ratings matrix, U: user factors, V: item factors
```

#### 8. **Deep Learning (Two-Tower thật)**
```python
# User Tower: [user_id, history, preferences] → embedding
# Item Tower: [place_id, tags, description] → embedding
# score = dot(user_embedding, item_embedding)
```

#### 9. **Context-Aware**
- Thêm context: thời gian, weather, user location
- Seasonal recommendations

---

## 📊 BENCHMARK

| Metric | Current | Target | Industry Standard |
|--------|---------|--------|-------------------|
| Precision@10 | 4.55% | **>20%** | 20-30% |
| NDCG@10 | 8.65% | **>30%** | 30-50% |
| Coverage | 9.81% | **>30%** | 30-50% |
| MAP | 4.98% | **>15%** | 15-25% |

---

## ✅ NHỮNG ĐIỂM TỐT

1. **System hoạt động stable** - Không crash, handle cold-start OK
2. **Diversity tốt (42.7%)** - Recommendations đa dạng
3. **Cold-start handling** - Có fallback cho users mới
4. **Response time nhanh** - Content-based rất fast

---

## 🎯 ROADMAP

### Phase 1: Quick Wins (1-2 ngày)
- [ ] Thu thập thêm user interactions (khuyến khích users rate/like)
- [ ] Fine-tune hyperparameters (boost user history, add popularity)
- [ ] Normalize tags (chuẩn hóa "Mountain"/"Mountains")

### Phase 2: Algorithm Update (1 tuần)
- [ ] Implement Collaborative Filtering (ALS/SVD)
- [ ] Hybrid: 60% CF + 40% Content
- [ ] Add negative feedback handling

### Phase 3: Advanced (2-4 tuần)
- [ ] Implement Matrix Factorization
- [ ] Add context-aware features
- [ ] A/B testing với users thật

---

## 📝 KẾT LUẬN

**Trạng thái hiện tại:** ❌ **CẦN CẢI THIỆN**

**Lý do chính:**
1. Dữ liệu quá ít (11 users, 8.5 interactions/user)
2. Content-Based Filtering không đủ mạnh
3. Tags không đủ discriminative

**Next steps:**
1. **Ngay:** Thu thập thêm 100+ user interactions
2. **Tuần này:** Implement Collaborative Filtering
3. **Tháng này:** Hybrid approach + A/B testing

**Potential:** Nếu có đủ data + CF, có thể đạt Precision@10 > 20% ✅

---

**Chi tiết kỹ thuật:**
- Xem `evaluation_results.json` cho số liệu đầy đủ
- Xem `evaluation_detailed.csv` cho kết quả từng user
- Code evaluation: `evaluate_recsys.py`
