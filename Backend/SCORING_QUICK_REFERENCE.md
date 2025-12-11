# Quick Reference: User Rating Algorithm

## 📊 Scoring Rules at a Glance

| Interaction | Points | Final Score | Description |
|------------|--------|-------------|-------------|
| 🔍 **Search Appear** | +0.5 | 0.0-10.0 | Place shows in similar search |
| ❤️ **Like** | →10.0 | 10.0 | User likes place (MAX) |
| 👎 **Dislike** | →1.0 | 1.0 | User dislikes place (MIN) |
| ⚡ **Quick Bounce** (<10s) | -2.0 | 0.0-10.0 | Not interested |
| 👀 **Moderate View** (10-60s) | +1.0 | 0.0-10.0 | Basic interest |
| 🔥 **Extended View** (>60s) | +2.0 | 0.0-10.0 | Strong interest |

## 🚀 Quick Start API Examples

### Track Watch Time
```bash
curl -X POST http://localhost:8000/rating/watch-time \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"place_id": 123, "watch_time_seconds": 45}'
```

### Track Like
```bash
curl -X POST http://localhost:8000/rating/interact \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"place_id": 123, "interaction_type": "like"}'
```

### Get My Ratings
```bash
curl -X GET http://localhost:8000/rating/my-ratings \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## 📈 Example Score Progression

```
0.0  → Search appears        → 0.5
0.5  → Views for 45s         → 1.5
1.5  → Appears in search     → 2.0
2.0  → Views for 90s         → 4.0
4.0  → User likes            → 10.0 ✅
```

## 🎯 Frontend Integration Checklist

- [x] **Automatic**: Search appears (handled by `/recommend` endpoint)
- [ ] **On Page Load**: Start watch time tracking
- [ ] **On Page Leave**: Send final watch time
- [ ] **Like Button**: Send `like` interaction
- [ ] **Dislike Button**: Send `dislike` interaction

## 💾 Database Schema

```sql
CREATE TABLE rating (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    place_id INTEGER NOT NULL,
    score REAL DEFAULT 0.0,
    FOREIGN KEY (user_id) REFERENCES user(id),
    FOREIGN KEY (place_id) REFERENCES place(id)
);
```

## 🔧 Key Functions (Backend)

```python
# In scoring_service.py
from app.services.scoring_service import (
    update_score_on_search_similarity,  # +0.5
    update_score_on_like,               # →10.0
    update_score_on_dislike,            # →1.0
    update_score_on_watch_time,         # Variable
    calculate_user_place_score          # One-shot calculation
)
```

## ⚠️ Important Notes

1. **Like/Dislike Override**: These set absolute scores (10.0 or 1.0) regardless of previous value
2. **Score Clamping**: All scores are clamped between 0.0 and 10.0
3. **Search Auto-Tracking**: Places in search results automatically get +0.5 when user is logged in
4. **Cumulative**: Most interactions add to existing score (except like/dislike)
5. **Watch Time**: Can be negative! Quick bounces subtract points

## 🎨 Frontend JavaScript Example

```javascript
// Track watch time (call every 10 seconds)
let watchStart = Date.now();
setInterval(async () => {
    const seconds = Math.floor((Date.now() - watchStart) / 1000);
    await fetch('/rating/watch-time', {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            place_id: currentPlaceId,
            watch_time_seconds: seconds
        })
    });
}, 10000);

// Track like
async function trackLike(placeId) {
    await fetch('/rating/interact', {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            place_id: placeId,
            interaction_type: 'like'
        })
    });
}
```

## 📚 Full Documentation

See `SCORING_ALGORITHM.md` for complete documentation including:
- Detailed scoring rules
- Migration guides
- Performance optimization
- Use cases for ML models
- Best practices

## 🧪 Testing

Run the test script to see scoring in action:
```bash
cd backend
python -m app.services.test_scoring_algorithm
```
