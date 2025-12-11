# Implementation Summary: User Rating & Scoring Algorithm

## ✅ What Was Implemented

A comprehensive user-place rating algorithm based on the following requirements:
- **Search similarity**: +0.5 points when place appears in search with similar themes
- **Like**: Sets score to 10.0 (maximum)
- **Dislike**: Sets score to 1.0 (minimum)
- **Watch time**:
  - Quick bounce (<10s): -2.0 points
  - Moderate time (10-60s): +1.0 point
  - Extended time (>60s): +2.0 points

## 📁 Files Modified

### 1. **app/services/scoring_service.py**
- ✅ Added `calculate_user_place_score()` - One-shot score calculation
- ✅ Added `update_score_on_search_similarity()` - +0.5 per search appearance
- ✅ Added `update_score_on_like()` - Set to 10.0
- ✅ Added `update_score_on_dislike()` - Set to 1.0
- ✅ Added `update_score_on_watch_time()` - Variable based on duration
- ✅ Kept legacy `calculate_interest_score()` for backward compatibility

### 2. **app/schemas.py**
- ✅ Extended `InteractionType` enum with:
  - `watch_time` - Track viewing duration
  - `search_appear` - Track search appearances
- ✅ Updated `InteractionCreate` with optional `watch_time_seconds` field
- ✅ Added `WatchTimeUpdate` schema for dedicated watch time endpoint
- ✅ Updated `RatingCreate` with watch time support

### 3. **app/routers/rating.py**
- ✅ Completely rewritten `/interact` endpoint with new scoring logic
- ✅ Added `/watch-time` endpoint for dedicated watch time tracking
- ✅ Added `/my-ratings` endpoint to get user's all ratings
- ✅ Added `/rating/{place_id}` endpoint to get specific place rating
- ✅ Implemented proper score calculation and clamping (0.0-10.0)
- ✅ Added validation for watch_time interaction
- ✅ Added detailed response with previous_score for debugging

### 4. **app/routers/recommendation.py**
- ✅ Added automatic search appearance tracking
- ✅ Imported `update_score_on_search_similarity` function
- ✅ Implemented batch scoring for all places in search results
- ✅ Awards +0.5 points to each place that appears in recommendations

## 📄 Files Created

### 1. **SCORING_ALGORITHM.md** (Main Documentation)
- Complete algorithm overview
- Database schema details
- Detailed scoring rules with examples
- API endpoint documentation
- Frontend integration guide with code examples
- Use cases for recommendation systems
- Best practices for backend/frontend/data science
- Migration notes for existing data
- Performance considerations
- Future enhancement ideas

### 2. **SCORING_QUICK_REFERENCE.md** (Quick Guide)
- At-a-glance scoring rules table
- Quick start API examples with curl commands
- Example score progression
- Frontend integration checklist
- Database schema
- Key functions reference
- JavaScript integration examples

### 3. **app/services/test_scoring_algorithm.py** (Test Script)
- Comprehensive test scenarios:
  - Progressive engagement
  - Quick bounce (negative signal)
  - Dislike scenario
  - Multiple searches
  - One-shot calculation
  - Watch time variations
  - Like override behavior
- Scoring rules summary table
- Can be run standalone to test algorithm

## 🔄 How It Works

### Automatic Tracking (No Frontend Changes Needed)
When a user searches using `/recommend` endpoint:
1. Backend processes the search query
2. Returns relevant places
3. **Automatically awards +0.5 points** to each place that appeared
4. Scores are updated in batch for performance

### Manual Tracking (Frontend Implementation Required)

#### Watch Time (Periodic Updates)
```javascript
// Every 10 seconds while viewing
fetch('/rating/watch-time', {
    method: 'POST',
    body: JSON.stringify({
        place_id: placeId,
        watch_time_seconds: elapsedSeconds
    })
});
```

#### Like/Dislike
```javascript
// When user clicks like button
fetch('/rating/interact', {
    method: 'POST',
    body: JSON.stringify({
        place_id: placeId,
        interaction_type: 'like'  // or 'dislike'
    })
});
```

## 📊 Database Structure

Uses existing `rating` table:
```
rating:
  - id (primary key)
  - user_id (foreign key → user.id)
  - place_id (foreign key → place.id)
  - score (float, 0.0-10.0)
```

**No database migration required** - uses existing schema!

## 🎯 Key Features

1. **Cumulative Scoring**: Most interactions add to existing score
2. **Override Mechanism**: Like/Dislike set absolute values
3. **Score Clamping**: Always between 0.0 and 10.0
4. **Negative Signals**: Quick bounces can reduce score
5. **Automatic Tracking**: Search appearances tracked without frontend code
6. **Batch Processing**: Efficient bulk updates for search results
7. **Backward Compatible**: Old `calculate_interest_score()` still works

## 🔍 Example Score Progression

```
User searches "beaches in Vietnam"
  → 5 beach places appear → Each gets +0.5 points

User views "Nha Trang Beach" for 45 seconds
  → Score: 0.5 → 1.5 (+1.0)

Place appears in another search
  → Score: 1.5 → 2.0 (+0.5)

User views for 2 minutes
  → Score: 2.0 → 4.0 (+2.0)

User clicks LIKE button
  → Score: 4.0 → 10.0 (override to max)
```

## ✨ Benefits

### For Recommendation System
- Rich implicit feedback from 0.0-10.0 scale
- Can train collaborative filtering models
- Identifies strong preferences (score ≥ 7.0)
- Identifies dislikes (score ≤ 2.0)
- Combines explicit (like/dislike) and implicit (clicks, time) signals

### For Users
- Personalized recommendations improve over time
- No manual rating required (mostly automatic)
- Quick interactions (clicks) still contribute
- Extended viewing sessions recognized and rewarded

### For Developers
- Clean, modular functions
- Easy to test and debug
- Documented extensively
- Performance optimized (batch updates)
- RESTful API design

## 🧪 Testing the Implementation

### Run Test Script
```bash
cd backend
python -m app.services.test_scoring_algorithm
```

This will output detailed scenarios showing how scores change.

### Test API Endpoints

1. **Start the backend server**
   ```bash
   cd backend
   uvicorn app.main:app --reload
   ```

2. **Login and get token**
   ```bash
   curl -X POST http://localhost:8000/auth/login \
     -d "username=testuser&password=testpass"
   ```

3. **Test interactions**
   ```bash
   # Track a click
   curl -X POST http://localhost:8000/rating/interact \
     -H "Authorization: Bearer YOUR_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"place_id": 1, "interaction_type": "click"}'

   # Get your ratings
   curl -X GET http://localhost:8000/rating/my-ratings \
     -H "Authorization: Bearer YOUR_TOKEN"
   ```

## 📚 Documentation Files

- **SCORING_ALGORITHM.md** - Complete reference (60+ sections)
- **SCORING_QUICK_REFERENCE.md** - Quick guide for developers
- **test_scoring_algorithm.py** - Executable test scenarios
- **This file** - Implementation summary

## 🚀 Next Steps (Frontend Integration)

1. **Add click tracking** to place cards/links
2. **Implement watch time tracker** using JavaScript timers
3. **Add like/dislike buttons** to place detail pages
4. **Display user's rating** on place cards (optional)
5. **Show personalization indicator** (e.g., "You might like this - 8.5/10")

## 🎓 Learning the System

1. Read **SCORING_QUICK_REFERENCE.md** first (5 min read)
2. Run **test_scoring_algorithm.py** to see it in action
3. Read **SCORING_ALGORITHM.md** for deep dive
4. Test API endpoints with curl/Postman
5. Integrate into frontend following examples

## 💡 Tips

- **Search tracking is automatic** - no need to call any endpoint
- **Batch watch time updates** every 10 seconds, not every second
- **Like/Dislike are final** - they override all previous scores
- **Negative scores are clamped** - minimum is 0.0, not negative
- **Use score ≥ 7.0** as "strong interest" for recommendations

## ✅ Validation Checklist

- [x] Scoring functions implemented with proper clamping
- [x] API endpoints created and tested
- [x] Automatic search tracking integrated
- [x] Database schema compatible (no migration needed)
- [x] Comprehensive documentation written
- [x] Test script created and verified
- [x] Quick reference guide created
- [x] Backend code has no errors
- [x] All interaction types supported
- [x] Watch time validation implemented

## 📞 Support

For questions or issues:
1. Check **SCORING_QUICK_REFERENCE.md** for quick answers
2. Read **SCORING_ALGORITHM.md** for detailed explanations
3. Run **test_scoring_algorithm.py** to see examples
4. Review code in **scoring_service.py** and **rating.py**

---

**Status**: ✅ Complete and Ready for Frontend Integration

**Last Updated**: December 11, 2025
