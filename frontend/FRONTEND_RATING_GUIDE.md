# Frontend Rating Integration Guide

## Overview

The frontend now includes a comprehensive rating system that tracks user interactions and sends them to the backend for scoring. This implementation follows the scoring algorithm documented in the backend.

## Files

### New Files
- **`src/js/rating-service.js`** - Core rating service with watch time tracking, like/dislike, and score management

### Modified Files
- **`src/js/detail.js`** - Added watch time tracking and like/dislike buttons on detail pages
- **`src/js/result.js`** - Updated like/dislike handlers to use rating service
- **`src/js/api.js`** - (Existing) Contains API communication functions

## Features Implemented

### ✅ Automatic Search Tracking
Search tracking is handled automatically by the backend when users search. No frontend code needed!

### ✅ Watch Time Tracking
- **Starts automatically** when user opens a place detail page
- **Updates every 10 seconds** with current viewing duration
- **Sends final time** when user leaves the page
- **Pauses/resumes** when user switches browser tabs

### ✅ Like/Dislike
- Click "Like" button → Score set to 10.0
- Click "Dislike" button → Score set to 1.0
- Buttons highlight based on user's existing rating
- Visual feedback with toast notifications

### ✅ Score Display
- User's existing ratings are loaded and applied to search results
- Like/dislike buttons show active state based on score
- Score updates displayed in real-time

## Usage

### In Detail Page (`detail.js`)

```javascript
import { ratingService } from './rating-service.js';

// Start watch time tracking when page loads
ratingService.startWatchTimeTracking(placeId);

// Track like
await ratingService.trackLike(placeId);

// Track dislike
await ratingService.trackDislike(placeId);

// Get user's rating for this place
const rating = await ratingService.getPlaceRating(placeId);
```

### In Results Page (`result.js`)

```javascript
import { ratingService } from './rating-service.js';

// Apply user's ratings to all results
if (ratingService.isLoggedIn()) {
    await ratingService.applyUserRatings();
}

// Like/dislike handlers automatically use ratingService
// (already implemented in handleLike and handleDislike functions)
```

## Rating Service API

### Core Methods

#### `trackLike(placeId)`
Track a like interaction. Sets score to 10.0.

```javascript
const result = await ratingService.trackLike(123);
// Returns: { status: "updated", score: 10.0, ... }
```

#### `trackDislike(placeId)`
Track a dislike interaction. Sets score to 1.0.

```javascript
const result = await ratingService.trackDislike(123);
// Returns: { status: "updated", score: 1.0, ... }
```

#### `startWatchTimeTracking(placeId)`
Start tracking how long user views a place. Updates every 10 seconds.

```javascript
ratingService.startWatchTimeTracking(123);
```

#### `stopWatchTimeTracking(placeId)`
Stop tracking and send final watch time.

```javascript
ratingService.stopWatchTimeTracking(123);
```

#### `getUserRatings()`
Get all user's ratings.

```javascript
const data = await ratingService.getUserRatings();
// Returns: { user_id: 1, total_ratings: 5, ratings: [...] }
```

#### `getPlaceRating(placeId)`
Get user's rating for a specific place.

```javascript
const data = await ratingService.getPlaceRating(123);
// Returns: { place_id: 123, score: 7.5 }
```

#### `applyUserRatings()`
Load and apply user's ratings to current page.

```javascript
await ratingService.applyUserRatings();
```

## How It Works

### Watch Time Flow

1. User opens `detail.html?id=123`
2. `detail.js` calls `ratingService.startWatchTimeTracking(123)`
3. Timer starts, tracking elapsed time
4. Every 10 seconds, sends update to `/api/v1/rating/watch-time`
5. When user leaves page, sends final time
6. Backend calculates score based on duration:
   - <10s: -2 points (quick bounce)
   - 10-60s: +1 point (moderate)
   - >60s: +2 points (extended)

### Like/Dislike Flow

1. User clicks "Like" button
2. `handleDetailLike()` or `handleLike()` called
3. Sends POST to `/api/v1/rating/interact` with `interaction_type: 'like'`
4. Backend sets score to 10.0
5. Button highlights green
6. Toast shows "Liked! Score: 10.0"

### Score Display Flow

1. Page loads (results or detail)
2. If user logged in, calls `ratingService.applyUserRatings()`
3. Fetches all user ratings from `/api/v1/rating/my-ratings`
4. For each place on page:
   - If score >= 7.0: highlight like button green
   - If score <= 2.0: highlight dislike button red

## Visual Feedback

### Toast Notifications
```javascript
// Success (green)
showRatingFeedback('Liked! Score: 10.0', 'success');

// Info (blue)
showRatingFeedback('Disliked. Score: 1.0', 'info');
```

### Button States
- **Active Like** (score >= 7.0): Green background, white icon
- **Active Dislike** (score <= 2.0): Red background, white icon
- **Neutral** (2.0 < score < 7.0): Default style

## HTML Structure

### Detail Page Rating Buttons
```html
<div class="detail-actions">
    <button class="detail-rating-btn like-btn" onclick="handleDetailLike(123)">
        <i class="fas fa-thumbs-up"></i> Like
    </button>
    <button class="detail-rating-btn dislike-btn" onclick="handleDetailDislike(123)">
        <i class="fas fa-thumbs-down"></i> Dislike
    </button>
</div>
```

### Result Card Rating Buttons
```html
<div class="card-footer">
    <button class="icon-action like-btn" onclick="handleLike(event, 123)">
        <i class="fas fa-thumbs-up"></i>
    </button>
    <button class="icon-action dislike-btn" onclick="handleDislike(event, 123)">
        <i class="fas fa-thumbs-down"></i>
    </button>
</div>
```

## CSS Styling (Add to your CSS files)

```css
/* Rating buttons on detail page */
.detail-rating-btn {
    padding: 10px 20px;
    border: 2px solid #ddd;
    background: white;
    border-radius: 5px;
    cursor: pointer;
    font-size: 1rem;
    transition: all 0.3s;
    margin: 0 5px;
}

.detail-rating-btn:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 8px rgba(0,0,0,0.1);
}

.detail-rating-btn.active.like-btn {
    background: #2ecc71;
    color: white;
    border-color: #2ecc71;
}

.detail-rating-btn.active.dislike-btn {
    background: #e74c3c;
    color: white;
    border-color: #e74c3c;
}

/* Toast animations */
@keyframes slideIn {
    from {
        transform: translateX(100%);
        opacity: 0;
    }
    to {
        transform: translateX(0);
        opacity: 1;
    }
}

@keyframes slideOut {
    from {
        transform: translateX(0);
        opacity: 1;
    }
    to {
        transform: translateX(100%);
        opacity: 0;
    }
}

/* Result card active states */
.icon-action.active {
    transform: scale(1.1);
}

.icon-action.like-btn.active {
    color: #2ecc71;
}

.icon-action.dislike-btn.active {
    color: #e74c3c;
}
```

## Browser Compatibility

- ✅ Chrome/Edge (Chromium)
- ✅ Firefox
- ✅ Safari
- ✅ Mobile browsers

**Required Features:**
- LocalStorage (for auth token)
- Fetch API
- ES6 Modules
- setInterval/clearInterval

## Debugging

### Enable Console Logs
The rating service logs all actions:

```javascript
✅ Tracked like for place 123: {...}
⏱️ Watch time updated for place 123: 45s, score: 2.5
▶️ Started watch time tracking for place 123
⏹️ Stopped watch time tracking for place 123 (45s total)
```

### Check Network Requests
Open DevTools → Network → Filter by "rating" to see:
- POST `/api/v1/rating/interact`
- POST `/api/v1/rating/watch-time`
- GET `/api/v1/rating/my-ratings`
- GET `/api/v1/rating/rating/123`

### Common Issues

**Watch time not tracking:**
- Check if user is logged in: `ratingService.isLoggedIn()`
- Check console for errors
- Verify token in localStorage

**Buttons not highlighting:**
- Check if `applyUserRatings()` was called
- Verify `data-place-id` attribute on cards
- Check user ratings: `await ratingService.getUserRatings()`

**Score not updating:**
- Check network response in DevTools
- Verify backend endpoint is `/api/v1/rating/interact`
- Check auth token is valid

## Performance

### Optimizations
- Watch time updates batched every 10 seconds (not every second)
- User ratings cached after first fetch
- Timer pauses when tab is hidden
- All timers cleaned up on page unload

### Network Usage
- Watch time: ~1 request per 10 seconds while viewing
- Like/Dislike: 1 request per action
- Load ratings: 1 request per page load
- Total: Very lightweight (<100 KB per session)

## Testing

### Manual Test Checklist

**Detail Page:**
1. [ ] Open detail page while logged in
2. [ ] Check console for "Started watch time tracking" message
3. [ ] Wait 10 seconds, check for "Watch time updated" message
4. [ ] Click Like button → turns green, shows toast
5. [ ] Click Dislike button → turns red, shows toast
6. [ ] Leave page → check for "Stopped watch time tracking" message

**Results Page:**
1. [ ] Open results page while logged in
2. [ ] Like a place → button turns green
3. [ ] Dislike a place → button turns red
4. [ ] Refresh page → buttons stay highlighted
5. [ ] Logout → buttons reset to default

**Watch Time Scoring:**
1. [ ] Open detail, leave immediately (<10s) → check score in DevTools
2. [ ] Open detail, stay 30s → check score increased
3. [ ] Open detail, stay 90s → check score increased more

## Future Enhancements

- [ ] Offline support with queue sync
- [ ] Real-time score updates via WebSockets
- [ ] Analytics dashboard showing user preferences
- [ ] A/B testing different update intervals
- [ ] Visual progress bar showing watch time
- [ ] Gamification (badges, achievements)

## Support

For issues or questions:
- Backend API: See `backend/SCORING_ALGORITHM.md`
- Frontend integration: See this file
- API endpoints: Check `backend/app/routers/rating.py`
