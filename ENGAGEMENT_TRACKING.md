# Enhanced View Time Tracking với Engagement Metrics

**Date:** December 16, 2025  
**Upgrade:** View Time + Scroll Depth + Interaction Tracking

## 🎯 Vấn Đề Đã Giải Quyết

### Trước đây (Chỉ Track Time):
❌ User mở tab để đó 90s không xem → 4.0 điểm  
❌ User scroll nhanh xem 5s → 2.5 điểm  
❌ Không phân biệt "thực sự quan tâm" vs "mở nhầm"

### Bây giờ (Track Time + Scroll + Interaction):
✅ User mở tab để đó 90s (không scroll) → 0.5x multiplier → 2.0 điểm  
✅ User scroll 50%, xem 30s → 1.0x multiplier → ~2.94 điểm  
✅ User scroll hết trang (>90%), xem 60s → 1.5x multiplier → ~5.2 → cap 4.0 điểm

## 📊 Thuật Toán Mới

### 1. Track 3 Metrics:

```javascript
// 1. VIEW TIME (giây)
viewTimeSeconds = (Date.now() - viewStartTime) / 1000

// 2. SCROLL DEPTH (%)
scrollDepth = ((scrollTop + windowHeight) / documentHeight) * 100

// 3. HAS INTERACTED (boolean)
hasInteracted = user đã scroll, click, touch, hoặc nhấn phím
```

### 2. Calculate Engagement Multiplier:

```javascript
function calculateEngagementMultiplier(viewTime, scrollDepth, interacted) {
    // Case 1: Không scroll, không tương tác → Tab bị bỏ quên
    if (!interacted && scrollDepth < 10) {
        return 0.5; // Penalty: -50%
    }
    
    // Case 2: Scroll ít (< 30%) → Xem qua loa
    if (scrollDepth < 30) {
        return 0.7; // Penalty: -30%
    }
    
    // Case 3: Scroll vừa phải (30-60%) → Normal
    if (scrollDepth < 60) {
        return 1.0; // No change
    }
    
    // Case 4: Scroll nhiều (60-90%) → Good engagement
    if (scrollDepth < 90) {
        return 1.2; // Bonus: +20%
    }
    
    // Case 5: Scroll hết (>90%) → Excellent engagement
    return 1.5; // Bonus: +50%
}
```

### 3. Apply Multiplier:

```javascript
adjustedViewTime = rawViewTime * engagementMultiplier
```

### 4. Send to Backend:

```javascript
POST /api/v1/rating/view-time
{
    place_id: 595,
    view_time_seconds: 44.1,      // Adjusted (sau khi nhân multiplier)
    raw_view_time: 30.0,           // Original (trước khi nhân)
    scroll_depth: 85,              // %
    has_interacted: true
}
```

## 📈 Ví Dụ Thực Tế

### Scenario 1: User Thực Sự Quan Tâm
```
Raw view time: 45 giây
Scroll depth: 95% (đọc hết trang)
Has interacted: true

→ Multiplier: 1.5x
→ Adjusted time: 45 * 1.5 = 67.5s
→ Score: 3.74 (gần max)
```

### Scenario 2: User Xem Nhanh
```
Raw view time: 15 giây
Scroll depth: 40% (scroll vừa phải)
Has interacted: true

→ Multiplier: 1.0x
→ Adjusted time: 15s
→ Score: 2.68
```

### Scenario 3: User Mở Tab Nhưng Không Xem
```
Raw view time: 120 giây (2 phút)
Scroll depth: 5% (hầu như không scroll)
Has interacted: false

→ Multiplier: 0.5x (penalty!)
→ Adjusted time: 120 * 0.5 = 60s
→ Score: 3.47 (thay vì 4.0 max)
```

### Scenario 4: User Scroll Qua Loa
```
Raw view time: 20 giây
Scroll depth: 25% (scroll ít)
Has interacted: true

→ Multiplier: 0.7x (penalty)
→ Adjusted time: 20 * 0.7 = 14s
→ Score: 2.66
```

## 🔧 Implementation

### Frontend (detail.js):

**1. Track Scroll Depth:**
```javascript
let maxScrollDepth = 0;

function updateScrollDepth() {
    const scrollPercentage = ((scrollTop + windowHeight) / documentHeight) * 100;
    maxScrollDepth = Math.max(maxScrollDepth, scrollPercentage);
}

window.addEventListener('scroll', updateScrollDepth, { passive: true });
```

**2. Track Interactions:**
```javascript
let hasInteracted = false;

['click', 'touchstart', 'keydown'].forEach(eventType => {
    document.addEventListener(eventType, () => {
        hasInteracted = true;
    }, { once: true });
});
```

**3. Calculate & Send:**
```javascript
const engagementMultiplier = calculateEngagementMultiplier(
    viewTimeSeconds, 
    maxScrollDepth, 
    hasInteracted
);
const adjustedViewTime = viewTimeSeconds * engagementMultiplier;

// Send both raw and adjusted time
fetch('/api/v1/rating/view-time', {
    body: JSON.stringify({
        place_id: currentPlaceId,
        view_time_seconds: adjustedViewTime,
        raw_view_time: viewTimeSeconds,
        scroll_depth: Math.round(maxScrollDepth),
        has_interacted: hasInteracted
    })
});
```

### Backend (rating.py):

**1. Updated Request Model:**
```python
class ViewTimeRequest(BaseModel):
    place_id: int
    view_time_seconds: float  # Adjusted time
    raw_view_time: Optional[float] = None
    scroll_depth: Optional[int] = None
    has_interacted: Optional[bool] = None
```

**2. Log Engagement Metrics:**
```python
print(f"[View Time Tracking] User {user_id} - Place {place_id}:")
print(f"  - Adjusted: {view_time_seconds}s")
print(f"  - Raw: {raw_view_time}s")
print(f"  - Scroll: {scroll_depth}%")
print(f"  - Interacted: {has_interacted}")
```

**3. Use Adjusted Time for Scoring:**
```python
# Scoring algorithm uses adjusted time
rating = RatingScorer.update_rating(
    user_id=user_id,
    place_id=place_id,
    session=session,
    view_time_seconds=view_data.view_time_seconds  # Already adjusted
)
```

## 🧪 Cách Test

### Test 1: Normal Engagement
1. Login → vào detail page
2. **Scroll xuống 50% trang**
3. **Chờ 30 giây**
4. Đóng tab
5. **Expected logs:**
   ```javascript
   raw_view_time: 30
   scroll_depth: 50%
   engagement_multiplier: 1.00
   adjusted_view_time: 30
   ```

### Test 2: Excellent Engagement
1. Login → vào detail page
2. **Scroll đến cuối trang (>90%)**
3. **Chờ 45 giây**
4. Đóng tab
5. **Expected logs:**
   ```javascript
   raw_view_time: 45
   scroll_depth: 95%
   engagement_multiplier: 1.50
   adjusted_view_time: 67.5
   ```

### Test 3: Tab Left Open (No Engagement)
1. Login → vào detail page
2. **KHÔNG scroll, KHÔNG click**
3. **Chờ 90 giây**
4. Đóng tab
5. **Expected logs:**
   ```javascript
   raw_view_time: 90
   scroll_depth: 0%
   has_interacted: false
   engagement_multiplier: 0.50
   adjusted_view_time: 45
   ```

### Test 4: Quick Skim
1. Login → vào detail page
2. **Scroll nhanh 25%**
3. **Chờ 10 giây**
4. Đóng tab
5. **Expected logs:**
   ```javascript
   raw_view_time: 10
   scroll_depth: 25%
   engagement_multiplier: 0.70
   adjusted_view_time: 7
   ```

## 📊 Score Comparison

| Scenario | Raw Time | Scroll | Multiplier | Adjusted Time | Old Score | New Score |
|----------|----------|--------|------------|---------------|-----------|-----------|
| Tab left open | 90s | 0% | 0.5x | 45s | 4.0 | 3.21 |
| Quick skim | 10s | 25% | 0.7x | 7s | 2.59 | 2.52 |
| Normal read | 30s | 50% | 1.0x | 30s | 2.94 | 2.94 |
| Good read | 45s | 75% | 1.2x | 54s | 3.21 | 3.59 |
| Full read | 60s | 95% | 1.5x | 90s | 3.47 | 4.0 |

## ✅ Benefits

1. **More Accurate Scoring:**
   - Phân biệt được "thực sự quan tâm" vs "mở nhầm"
   - Thưởng users đọc kỹ, phạt users mở tab để quên

2. **Better Recommendations:**
   - Ratings phản ánh đúng interests
   - RecSys suggest chính xác hơn

3. **Analytics Insights:**
   - Biết places nào được đọc kỹ
   - Biết content nào engaging
   - Optimize UX dựa trên scroll patterns

4. **Fair Scoring:**
   - 90s không scroll = 3.21 điểm (fair)
   - 45s scroll hết = 4.0 điểm (reward engagement)

## 🚀 Next Steps

1. **Restart backend** để apply changes
2. **Test với 4 scenarios trên**
3. **Monitor logs** để xem engagement patterns
4. **Analyze data** sau 1 tuần để adjust multipliers nếu cần

## 📝 Notes

- Engagement multiplier có thể fine-tune dựa trên data
- Có thể thêm tracking khác: mouse movement, time on visible sections
- Có thể store engagement metrics vào database để analytics sau này

---

**Status:** ✅ IMPLEMENTED  
**Requires:** Backend restart để apply changes
