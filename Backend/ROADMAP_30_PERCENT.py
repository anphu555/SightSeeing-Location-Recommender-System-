"""
ROADMAP ĐẠT 30% PRECISION@10

Hiện tại: 17.63%
Mục tiêu: 30%
Gap: +12.37% (cần tăng ~70%)

=== PHÂN TÍCH ===

Với 552 users, có thể implement full collaborative filtering!

Current approach:
- ✅ Content-based (TF-IDF)
- ✅ Item-based CF (đã có)
- ❌ User-based CF (chưa có)
- ❌ Matrix Factorization (chưa có)
- ❌ Temporal features (chưa có)

=== CHIẾN LƯỢC ĐẠT 30% ===

PHASE 1: Enhanced Collaborative Filtering (+5-7%)
----------------------------------------------
1. **User-based CF** (NEW)
   - Build user-user similarity matrix
   - Find k-nearest neighbors
   - Recommend items liked by similar users
   - Expected gain: +3-4%

2. **Matrix Factorization** 
   - SVD hoặc ALS (đơn giản hơn implicit)
   - Learn latent factors
   - Dot product để predict scores
   - Expected gain: +2-3%

3. **Better CF Weighting**
   - Current: 50% CF
   - Increase to 60-65% CF (stronger personalization)
   - Expected gain: +1%

PHASE 2: Feature Engineering (+3-4%)
------------------------------------
1. **Popularity Decay**
   - Time-decay popularity (recent ratings weigh more)
   - Avoid over-recommending old popular items
   - Expected gain: +1-2%

2. **Tag Embeddings**
   - Word2Vec trên tag sequences
   - Capture semantic similarity
   - "Beach" → similar to "Coastal", "Seafood"
   - Expected gain: +2-3%

PHASE 3: Improved Re-ranking (+2-3%)
------------------------------------
1. **Diversity-aware scoring**
   - MMR (Maximal Marginal Relevance)
   - Balance relevance vs diversity
   - Expected gain: +1%

2. **Score calibration**
   - Normalize scores across users
   - Handle user rating bias
   - Expected gain: +1-2%

PHASE 4: Advanced Tuning (+1-2%)
--------------------------------
1. **Hyperparameter optimization**
   - Grid search trên weights
   - Cross-validation
   - Expected gain: +1%

2. **Ensemble methods**
   - Combine multiple models
   - Weighted voting
   - Expected gain: +1%

=== ROADMAP CỤ THỂ ===

Week 1: Collaborative Filtering
- [ ] Implement user-user similarity
- [ ] Add user-based CF scores
- [ ] Integrate into hybrid scoring
- Target: 17.63% → 21-22%

Week 2: Matrix Factorization
- [ ] Implement SVD với surprise library
- [ ] Train MF model
- [ ] Blend MF scores
- Target: 21-22% → 24-25%

Week 3: Feature Engineering
- [ ] Tag embeddings (Word2Vec)
- [ ] Popularity decay
- [ ] Better content features
- Target: 24-25% → 27-28%

Week 4: Final Tuning
- [ ] Hyperparameter optimization
- [ ] Diversity re-ranking
- [ ] Ensemble
- Target: 27-28% → 30%+

=== TECHNICAL IMPLEMENTATION ===

1. User-based CF:
```python
# Build user-user similarity
user_item_matrix = sparse_matrix(users x items)
user_similarity = cosine_similarity(user_item_matrix)

# Recommend
for similar_user in top_k_similar_users:
    recommend items_liked_by_similar_user
```

2. Matrix Factorization (SVD):
```python
from surprise import SVD, Dataset, Reader

# Build dataset
reader = Reader(rating_scale=(1, 5))
data = Dataset.load_from_df(ratings_df, reader)

# Train SVD
svd = SVD(n_factors=50, n_epochs=20)
svd.fit(data.build_full_trainset())

# Predict
score = svd.predict(user_id, place_id).est
```

3. Hybrid Scoring (NEW):
```python
# 4 signals instead of 3
score = (
    0.25 * content_score +
    0.30 * item_cf_score +
    0.30 * user_cf_score +  # NEW
    0.15 * popularity_score
)
```

=== RỦI RO & GIỚI HẠN ===

Rủi ro:
- User-based CF có thể slow với 552 users
- Matrix Factorization cần tune carefully
- Overfitting nếu không validate properly

Giải pháp:
- Cache similarity matrices
- Use incremental SVD
- Cross-validation để validate

Giới hạn:
- Không có temporal data → không thể time-aware
- Không có user demographics → không thể demographic-based
- Cold-start users vẫn khó

=== TIMELINE & EFFORT ===

| Phase | Effort | Expected Result | Cumulative |
|-------|--------|----------------|------------|
| Current | - | 17.63% | 17.63% |
| Phase 1 | 2-3 days | +5-7% | 22-24% |
| Phase 2 | 2-3 days | +3-4% | 25-28% |
| Phase 3 | 1-2 days | +2-3% | 27-31% |
| Phase 4 | 1 day | +1-2% | 28-32% |
| **Total** | **1-2 weeks** | **+10-14%** | **28-32%** ✅ |

=== KẾT LUẬN ===

✅ **FEASIBLE** - Có thể đạt 30% với:
- Enhanced Collaborative Filtering
- Tag embeddings
- Better feature engineering
- Proper tuning

✅ **RECOMMENDED APPROACH**:
1. Start with User-based CF (biggest impact, ~+4%)
2. Add Matrix Factorization (+3%)
3. Tag embeddings (+2-3%)
4. Fine-tune (+1-2%)

Total: ~30%+ Precision@10

⚠️ **CHÚ Ý**: 
- Cần validate trên separate test set
- Avoid overfitting
- Monitor diversity (đang thấp: 8.18%)

🎯 **NEXT STEPS**:
Implement Phase 1 (User-based CF) ngay để test xem gain thực tế bao nhiêu.
"""

print(__doc__)
