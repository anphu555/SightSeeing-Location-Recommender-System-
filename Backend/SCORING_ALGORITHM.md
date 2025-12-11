# User Rating & Scoring Algorithm

## Overview

This document describes the user-place rating algorithm that tracks user interactions and calculates cumulative scores based on various signals. The algorithm uses a scale of 0.0 to 10.0 to represent user interest in places.

## Database Schema

### Rating Table
- **user_id**: Foreign key to User table
- **place_id**: Foreign key to Place table
- **score**: Float (0.0 - 10.0) - Cumulative score based on interactions

## Scoring Rules

The algorithm tracks multiple types of interactions and updates scores accordingly:

| Interaction Type | Score Change | Final Score Range | Description |
|-----------------|--------------|-------------------|-------------|
| **search_appear** | +0.5 | 0.0 - 10.0 | Place appeared in search results with similar themes |
| **like** | Set to 10.0 | 10.0 (fixed) | User explicitly liked the place (maximum interest) |
| **dislike** | Set to 1.0 | 1.0 (fixed) | User explicitly disliked the place (minimum interest) |
| **watch_time** | Variable | 0.0 - 10.0 | Based on time spent viewing the place |

### Watch Time Scoring Details

Watch time is calculated based on the duration a user spends viewing a place:

- **Quick Bounce** (<10 seconds): **-2.0 points**
  - Indicates user wasn't interested
  - Can reduce score below initial value
  
- **Moderate Engagement** (10-60 seconds): **+1.0 point**
  - Shows basic interest
  - User spent enough time to read basic information
  
- **Strong Engagement** (>60 seconds): **+2.0 points**
  - Shows significant interest
  - User thoroughly explored the place details

## Score Calculation Flow

### Priority System

1. **Explicit Feedback (Highest Priority)**
   - `like` → Score = 10.0 (overrides all previous scores)
   - `dislike` → Score = 1.0 (overrides all previous scores)

2. **Implicit Feedback (Cumulative)**
   - `search_appear` → Current Score + 0.5
   - `click` → Current Score + 1.0
   - `watch_time` → Current Score + (-2.0, 1.0, or 2.0)

### Example Score Progression

```
Initial: 0.0
→ Search appears with beach theme: 0.5
→ User views for 45 seconds: 1.5
→ Place appears in another search: 2.0
→ User views for 2 minutes: 4.0
→ User likes the place: 10.0 (final)
```

### Negative Score Example

```
Initial: 0.0
→ User views for 5 seconds (quick bounce): 0.0 (0.0 - 2.0, clamped to 0.0)
→ Place appears in search: 0.5
→ User dislikes: 1.0 (final)
```

## API Endpoints

### 1. Track General Interaction
```http
POST /rating/interact
Authorization: Bearer {token}
Content-Type: application/json

{
  "place_id": 123,
  "interaction_type": "click",
  "watch_time_seconds": null  // Only required for watch_time interaction
}
```

**Interaction Types:**
- `search_appear` - Place appeared in search results
- `like` - User liked place
- `dislike` - User disliked place
- `watch_time` - Track viewing duration (requires `watch_time_seconds`)

**Response:**
```json
{
  "status": "updated",
  "score": 2.5,
  "interaction_type": "click",
  "previous_score": 1.5
}
```

### 2. Track Watch Time (Dedicated Endpoint)
```http
POST /rating/watch-time
Authorization: Bearer {token}
Content-Type: application/json

{
  "place_id": 123,
  "watch_time_seconds": 45
}
```

**Response:**
```json
{
  "status": "updated",
  "score": 3.5,
  "watch_time_seconds": 45,
  "previous_score": 2.5
}
```

### 3. Get User's Ratings
```http
GET /rating/my-ratings
Authorization: Bearer {token}
```

**Response:**
```json
{
  "user_id": 1,
  "total_ratings": 5,
  "ratings": [
    {"place_id": 123, "score": 10.0},
    {"place_id": 456, "score": 3.5},
    {"place_id": 789, "score": 1.0}
  ]
}
```

### 4. Get Rating for Specific Place
```http
GET /rating/rating/{place_id}
Authorization: Bearer {token}
```

**Response:**
```json
{
  "place_id": 123,
  "score": 7.5
}
```

## Frontend Integration Guide

### 1. Automatic Search Tracking
Search tracking is **automatically handled** by the recommendation endpoint. When a user searches, all returned places receive +0.5 points automatically.

```javascript
// No additional code needed - handled by backend
const response = await fetch('/recommend', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    user_text: "beaches in Vietnam",
    top_k: 10
  })
});
```

### 2. Track Watch Time
```javascript
let startTime = Date.now();
let watchInterval;

function startWatchTracking(placeId) {
  watchInterval = setInterval(() => {
    const watchTime = Math.floor((Date.now() - startTime) / 1000);
    
    // Update watch time every 10 seconds
    if (watchTime % 10 === 0) {
      fetch('/rating/watch-time', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          place_id: placeId,
          watch_time_seconds: watchTime
        })
      });
    }
  }, 1000);
}

function stopWatchTracking(placeId) {
  clearInterval(watchInterval);
  
  // Send final watch time
  const finalWatchTime = Math.floor((Date.now() - startTime) / 1000);
  fetch('/rating/watch-time', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      place_id: placeId,
      watch_time_seconds: finalWatchTime
    })
  });
}
```

### 3. Track Like/Dislike
```javascript
function onLike(placeId) {
  fetch('/rating/interact', {
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

function onDislike(placeId) {
  fetch('/rating/interact', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      place_id: placeId,
      interaction_type: 'dislike'
    })
  });
}
```

## Use Cases for Recommendation System

The scoring system supports multiple recommendation strategies:

### 1. Collaborative Filtering
Use the `score` field (0.0-10.0 scale) to train collaborative filtering models:
- Filter ratings with `score >= 7.0` as "positive" interactions
- Filter ratings with `score <= 3.0` as "negative" interactions
- Use scores directly for matrix factorization

### 2. Content-Based Filtering
Combine scores with place themes:
- Extract themes from highly-rated places (`score >= 7.0`)
- Find similar places with matching themes
- Boost recommendations with existing positive scores

### 3. Hybrid Approach
Currently implemented in `/recommend` endpoint:
- Uses user's rating history to extract preferred themes
- Combines with current search intent
- Filters places with negative scores (`score <= 2.0`)

## Best Practices

### For Backend Developers
1. **Always clamp scores** between 0.0 and 10.0
2. **Batch updates** when processing multiple interactions
3. **Use transactions** to ensure data consistency
4. **Index** user_id and place_id columns for performance

### For Frontend Developers
1. **Track search appearances** automatically (handled by backend)
2. **Track clicks** immediately when user navigates
3. **Track watch time** periodically (every 10 seconds recommended)
4. **Debounce** watch time updates to reduce server load
5. **Handle offline scenarios** - queue interactions and sync later

### For Data Scientists
1. **Filter noise** - scores below 1.0 might indicate bounces
2. **Weight recent interactions** more heavily in models
3. **Consider score velocity** - how quickly a score increases
4. **Normalize scores** across users if needed

## Migration Notes

If you have existing ratings in the database:

1. **Old scores were on a different scale** (like: 5.0, view: 3.0, click: 1.0, dislike: -1.0)
2. **New scale is 0.0-10.0** with cumulative scoring
3. **Migration strategy:**
   - Like (5.0) → 10.0
   - View (3.0) → 5.0
   - Click (1.0) → 1.0
   - Dislike (-1.0) → 1.0

```sql
-- Example migration SQL
UPDATE rating 
SET score = CASE 
    WHEN score >= 5.0 THEN 10.0  -- Old likes
    WHEN score >= 3.0 THEN 5.0   -- Old views
    WHEN score <= 0.0 THEN 1.0   -- Old dislikes
    ELSE score                    -- Keep as is
END;
```

## Performance Considerations

### Database Indexing
```sql
CREATE INDEX idx_rating_user_place ON rating(user_id, place_id);
CREATE INDEX idx_rating_user_score ON rating(user_id, score);
CREATE INDEX idx_rating_place_score ON rating(place_id, score);
```

### Caching Strategy
- Cache user's top-rated places (score >= 7.0)
- Cache frequently appearing search themes
- Invalidate cache on like/dislike events

### Scaling
- Consider partitioning ratings table by user_id
- Use read replicas for recommendation queries
- Batch process search appearances asynchronously

## Future Enhancements

Potential improvements to the scoring algorithm:

1. **Time Decay**: Reduce old scores over time
2. **Context Awareness**: Different scoring based on time of day, season
3. **Social Signals**: Incorporate ratings from similar users
4. **A/B Testing**: Test different scoring weights
5. **Personalized Weights**: Adjust scoring rules per user segment

## Support

For questions or issues, please refer to:
- Main README: `../README.md`
- Database Schema: `app/schemas.py`
- Scoring Service: `app/services/scoring_service.py`
- Rating Endpoints: `app/routers/rating.py`
