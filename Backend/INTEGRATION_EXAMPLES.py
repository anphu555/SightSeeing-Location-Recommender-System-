"""
Example usage of the Rating Scoring Algorithm

This file demonstrates how to use the new rating scoring system in your application.
"""

# Example 1: User views a place for 60 seconds
"""
Frontend code (JavaScript):
```javascript
// Track when user enters place detail page
const startTime = Date.now();

// When user leaves, calculate view time
window.addEventListener('beforeunload', async () => {
    const viewTimeSeconds = (Date.now() - startTime) / 1000;
    
    // Send to backend
    await fetch('/rating/view-time', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
            place_id: currentPlaceId,
            view_time_seconds: viewTimeSeconds
        })
    });
});
```

Backend response:
{
    "user_id": 1,
    "place_id": 123,
    "score": 2.59,  // Calculated from 60 seconds view time
    "status": "created"
}
"""

# Example 2: User likes a place
"""
Frontend code (JavaScript):
```javascript
async function likePlace(placeId) {
    const response = await fetch('/likes/place', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
            place_id: placeId,
            is_like: true
        })
    });
    
    return await response.json();
}

// Usage
const result = await likePlace(123);
// Rating automatically updated: +4 points
```

Backend automatically updates rating:
- Current score: 2.59
- After like: 2.59 + 4 = 5.0 (max)
"""

# Example 3: User dislikes a place
"""
Frontend code (JavaScript):
```javascript
async function dislikePlace(placeId) {
    const response = await fetch('/likes/place', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
            place_id: placeId,
            is_like: false
        })
    });
    
    return await response.json();
}

// Usage
const result = await dislikePlace(123);
// Rating automatically updated: -5 points or min 1.0
```

Backend automatically updates rating:
- Current score: 3.0
- After dislike: 3.0 - 5 = 1.0 (min)
"""

# Example 4: User comments on a place
"""
Frontend code (JavaScript):
```javascript
async function createComment(placeId, content) {
    const response = await fetch('/comments', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
            place_id: placeId,
            content: content
        })
    });
    
    return await response.json();
}

// Usage
const result = await createComment(123, "Great place!");
// Rating automatically updated: +0.5 points (first comment only)
```

Backend automatically updates rating:
- Current score: 3.0
- After first comment: 3.0 + 0.5 = 3.5
- After second comment: 3.5 (no change)
"""

# Example 5: Get current rating for a place
"""
Frontend code (JavaScript):
```javascript
async function getUserRating(placeId) {
    const response = await fetch(`/rating/rating/${placeId}`, {
        method: 'GET',
        headers: {
            'Authorization': `Bearer ${token}`
        }
    });
    
    return await response.json();
}

// Usage
const rating = await getUserRating(123);
console.log(rating);
// { "place_id": 123, "score": 4.5, "user_id": 1 }
```
"""

# Example 6: Complete user journey
"""
Complete flow for a user interacting with a place:

1. User clicks on place card (quick view: 3 seconds)
   -> No rating created (< 5 seconds = accidental click)

2. User opens place detail page and reads for 90 seconds
   -> POST /rating/view-time with view_time_seconds=90
   -> Rating created: 3.35 points

3. User writes a comment
   -> POST /comments
   -> Rating updated: 3.35 + 0.5 = 3.85 points

4. User likes the place
   -> POST /likes/place with is_like=true
   -> Rating updated: 3.85 + 4 = 5.0 points (max)

5. User returns later and views again for 120 seconds
   -> POST /rating/view-time with view_time_seconds=120
   -> Rating NOT changed (already has rating: 5.0)

6. User changes mind and dislikes
   -> POST /likes/place with is_like=false
   -> Rating updated: 5.0 - 5 = 1.0 points (min)
"""

# Backend Python example (if you need to use it programmatically)
"""
```python
from app.services.scoring_service import RatingScorer
from app.database import get_session

# Get database session
with get_session() as session:
    # Update rating based on view time
    rating = RatingScorer.update_rating(
        user_id=1,
        place_id=123,
        session=session,
        view_time_seconds=90.5
    )
    print(f"Rating after view: {rating.score}")
    
    # Update rating based on like
    rating = RatingScorer.update_rating(
        user_id=1,
        place_id=123,
        session=session,
        is_like=True
    )
    print(f"Rating after like: {rating.score}")
    
    # Update rating based on comment
    rating = RatingScorer.update_rating(
        user_id=1,
        place_id=123,
        session=session,
        has_commented=True
    )
    print(f"Rating after comment: {rating.score}")
    
    # Calculate score without updating database
    score = RatingScorer.calculate_rating_score(
        user_id=1,
        place_id=123,
        session=session,
        view_time_seconds=60,
        is_like=True,
        has_commented=True
    )
    print(f"Calculated score: {score}")
```
"""

print("See examples above for integration guidance!")
