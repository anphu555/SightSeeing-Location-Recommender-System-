# Frontend Rating Integration Checklist

## ✅ Pre-Deployment Checklist

### 1. File Imports
Add the rating CSS to your HTML files:

#### In `detail.html`:
```html
<head>
    ...
    <link rel="stylesheet" href="src/css/rating.css">
</head>
```

#### In `results.html` (or `result.html`):
```html
<head>
    ...
    <link rel="stylesheet" href="src/css/rating.css">
</head>
```

### 2. Module Imports
The rating service is already imported in:
- ✅ `detail.js` (line 3)
- ✅ `result.js` (line 2)

### 3. API Endpoint Configuration
Verify your `config.js` has the correct API base URL:

```javascript
// src/js/config.js
export const CONFIG = {
    apiBase: 'http://localhost:8000'  // Change for production
};
```

### 4. Backend API Endpoints
Ensure these endpoints are available:
- ✅ `POST /api/v1/rating/interact`
- ✅ `POST /api/v1/rating/watch-time`
- ✅ `GET /api/v1/rating/my-ratings`
- ✅ `GET /api/v1/rating/rating/{place_id}`

### 5. Authentication
Verify token storage works:
```javascript
// Should store token on login
localStorage.setItem('token', 'your-jwt-token');
localStorage.setItem('username', 'user123');

// Should clear on logout
localStorage.clear();
```

## 🧪 Testing Steps

### Step 1: Detail Page Watch Time
1. Login to your app
2. Open browser DevTools → Console
3. Navigate to `detail.html?id=1`
4. **Expected**: Console logs "▶️ Started watch time tracking for place 1"
5. Wait 10 seconds
6. **Expected**: Console logs "⏱️ Watch time updated for place 1: 10s, score: X"
7. Leave the page
8. **Expected**: Console logs "⏹️ Stopped watch time tracking for place 1 (Xs total)"

### Step 2: Detail Page Like/Dislike
1. On detail page, verify Like and Dislike buttons appear
2. Click **Like** button
3. **Expected**: 
   - Button turns green
   - Toast notification: "Liked! Score: 10.0"
   - Console log: "✅ Tracked like for place 1: ..."
4. Refresh page
5. **Expected**: Like button still green

### Step 3: Results Page Ratings
1. Navigate to `results.html`
2. Search for places
3. **Expected**: Places appear with Like/Dislike buttons
4. Click Like on a place card
5. **Expected**:
   - Button turns green
   - Toast notification appears
   - Button stays green after refresh

### Step 4: Score Persistence
1. Like a place (score → 10.0)
2. Close browser
3. Open browser and login again
4. Navigate to same place
5. **Expected**: Like button is still highlighted green

### Step 5: Watch Time Scoring
1. Open detail page, leave immediately (<10s)
2. Check Network tab → watch-time request
3. **Expected**: Score decreases (-2 points) or stays at 0
4. Open another place, stay for 45 seconds
5. **Expected**: Score increases (+1 point)
6. Open another place, stay for 90 seconds
7. **Expected**: Score increases (+2 points)

## 🔍 Debugging Checklist

### Console Errors?
- [ ] Check if `rating-service.js` is imported correctly
- [ ] Verify `CONFIG.apiBase` is correct
- [ ] Check browser console for import errors

### Watch Time Not Tracking?
- [ ] User is logged in? Check `localStorage.getItem('token')`
- [ ] Check console for "Started watch time tracking" message
- [ ] Verify Network tab shows POST requests every 10s

### Buttons Not Appearing?
- [ ] Check if `.detail-actions` element exists in HTML
- [ ] Verify JavaScript is executing (check console)
- [ ] Check if user is logged in

### Ratings Not Persisting?
- [ ] Check Network tab for successful API responses
- [ ] Verify backend is saving ratings to database
- [ ] Check localStorage for valid token

### Styling Issues?
- [ ] Verify `rating.css` is linked in HTML
- [ ] Check browser DevTools → Elements for class names
- [ ] Clear browser cache

## 📱 Cross-Browser Testing

Test on:
- [ ] Chrome/Edge (latest)
- [ ] Firefox (latest)
- [ ] Safari (latest)
- [ ] Mobile Chrome (Android)
- [ ] Mobile Safari (iOS)

## 🚀 Deployment Steps

### Development
```bash
# Start frontend dev server
cd frontend/exSighting
npm run dev
```

### Production Build
```bash
# Build frontend
npm run build

# Deploy to server
# Copy dist/ folder to web server
```

### Environment Variables
Update API base URL for production:

```javascript
// src/js/config.js
export const CONFIG = {
    apiBase: process.env.VITE_API_URL || 'https://api.yoursite.com'
};
```

## 📊 Monitoring

### What to Monitor
- Watch time API calls frequency (should be ~6/minute per user)
- Like/Dislike success rate
- Average watch time per place
- Rating distribution (how many 10s, 1s, etc.)

### Analytics Events
Consider adding:
```javascript
// Example: Google Analytics
gtag('event', 'place_liked', {
    place_id: placeId,
    score: result.score
});

gtag('event', 'watch_time', {
    place_id: placeId,
    duration: watchTimeSeconds
});
```

## ✅ Final Verification

Before going live, verify:

- [ ] Rating buttons appear on detail pages
- [ ] Rating buttons appear on result cards
- [ ] Watch time tracking starts automatically
- [ ] Like/Dislike updates score correctly
- [ ] Scores persist after refresh
- [ ] Toast notifications display properly
- [ ] Mobile responsive design works
- [ ] Console has no errors
- [ ] API endpoints return correct data
- [ ] Backend receives and stores ratings

## 📞 Troubleshooting

### Issue: "Import not found"
**Solution**: Ensure file paths are correct in imports
```javascript
import { ratingService } from './rating-service.js';  // Correct
import { ratingService } from 'rating-service.js';    // Wrong
```

### Issue: "CORS error"
**Solution**: Update backend CORS settings
```python
# In backend main.py or similar
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Issue: "401 Unauthorized"
**Solution**: Check if token is valid
```javascript
// Verify token exists and is not expired
const token = localStorage.getItem('token');
console.log('Token:', token);

// Re-login if needed
```

### Issue: Watch time not updating
**Solution**: Check timer is active
```javascript
// In console
console.log(ratingService.watchTimers);
// Should show Map with placeId -> timer object
```

## 🎉 Success Criteria

Your integration is successful when:

1. ✅ Users can like/dislike places
2. ✅ Watch time is tracked automatically
3. ✅ Scores persist across sessions
4. ✅ UI updates in real-time
5. ✅ No console errors
6. ✅ Mobile responsive
7. ✅ Performance is good (<100ms interactions)

## 📚 Next Steps After Integration

1. Monitor user behavior in analytics
2. Collect feedback on rating experience
3. Optimize update intervals based on usage
4. Add advanced features (see IMPLEMENTATION_COMPLETE.md)
5. Consider A/B testing different UI variations

---

**Questions?** See `FRONTEND_RATING_GUIDE.md` for detailed documentation.
