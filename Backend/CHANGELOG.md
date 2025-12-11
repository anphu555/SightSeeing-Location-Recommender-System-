# Changelog - User Rating & Scoring Algorithm

## [1.0.0] - 2025-12-11

### Added - Complete User-Place Rating System

#### Core Features
- **Automatic Search Tracking**: Places appearing in search results automatically receive +0.5 points
- **Click Tracking**: User clicks on places add +1.0 point
- **Like/Dislike System**: 
  - Like sets score to 10.0 (maximum interest)
  - Dislike sets score to 1.0 (minimum interest)
- **Watch Time Tracking**:
  - Quick bounce (<10s): -2.0 points
  - Moderate time (10-60s): +1.0 point
  - Extended time (>60s): +2.0 points
- **Score Clamping**: All scores bounded between 0.0 and 10.0

#### New Files

**Services**
- `backend/app/services/scoring_service.py` - Updated with 6 new scoring functions
- `backend/app/services/test_scoring_algorithm.py` - Comprehensive test suite

**Routers**
- `backend/app/routers/rating.py` - Completely rewritten with new endpoints

**Documentation**
- `backend/SCORING_ALGORITHM.md` - Complete reference (60+ sections)
- `backend/SCORING_QUICK_REFERENCE.md` - Quick start guide
- `backend/IMPLEMENTATION_SUMMARY.md` - Implementation overview
- `backend/SCORING_FLOW_DIAGRAM.md` - Visual flow diagrams
- `backend/CHANGELOG.md` - This file

#### Updated Files

**Schemas**
- `backend/app/schemas.py`
  - Added `watch_time` to `InteractionType` enum
  - Added `search_appear` to `InteractionType` enum
  - Added `watch_time_seconds` field to `InteractionCreate`
  - Created new `WatchTimeUpdate` schema
  - Updated `RatingCreate` documentation

**Routers**
- `backend/app/routers/recommendation.py`
  - Added automatic search appearance tracking
  - Batch score updates for all places in results
  - Imported `update_score_on_search_similarity`

**Documentation**
- `README.md` - Added scoring algorithm section with quick links

#### New API Endpoints

**POST /rating/interact**
- Tracks user interactions (click, like, dislike, search_appear, watch_time)
- Returns updated score with previous score for debugging
- Validates watch_time_seconds for watch_time interactions

**POST /rating/watch-time**
- Dedicated endpoint for tracking viewing duration
- Accepts watch_time_seconds parameter
- Returns score progression

**GET /rating/my-ratings**
- Retrieves all ratings for authenticated user
- Returns user_id, total count, and rating list

**GET /rating/rating/{place_id}**
- Gets specific place rating for authenticated user
- Returns current score or null if no rating exists

#### New Service Functions

**In scoring_service.py:**
1. `calculate_user_place_score()` - One-shot score calculation from all signals
2. `update_score_on_search_similarity()` - Add 0.5 per search appearance
3. `update_score_on_click()` - Add 1.0 per click
4. `update_score_on_like()` - Set to 10.0 (max)
5. `update_score_on_dislike()` - Set to 1.0 (min)
6. `update_score_on_watch_time()` - Variable based on duration

#### Backward Compatibility
- Kept `calculate_interest_score()` for legacy support (marked deprecated)
- No database migration required - uses existing `rating` table
- Old `InteractionType.view` still supported (treated as 30s watch time)

### Technical Details

#### Algorithm Design
- **Priority System**: Explicit feedback (like/dislike) overrides implicit signals
- **Cumulative Scoring**: Most interactions add to existing score
- **Negative Signals**: Quick bounces can reduce score (with floor at 0.0)
- **Batch Processing**: Search appearances updated in bulk for performance

#### Performance Optimizations
- Batch database updates for search results
- Single query per interaction
- Efficient score clamping
- Minimal database round trips

#### Database Impact
- **No schema changes required**
- Uses existing `rating` table:
  - `user_id` (FK to user)
  - `place_id` (FK to place)
  - `score` (float, 0.0-10.0)
- Recommended indexes:
  - `idx_rating_user_place` on (user_id, place_id)
  - `idx_rating_user_score` on (user_id, score)

### Documentation

#### Comprehensive Guides
- **SCORING_ALGORITHM.md**: 400+ lines covering:
  - Complete API reference
  - Frontend integration guide
  - Use cases for ML models
  - Performance optimization
  - Migration strategies
  - Best practices

- **SCORING_QUICK_REFERENCE.md**: Quick start guide with:
  - Scoring rules table
  - API examples (curl)
  - JavaScript integration
  - Frontend checklist

- **IMPLEMENTATION_SUMMARY.md**: Implementation details:
  - What was built
  - How it works
  - Example flows
  - Testing guide

- **SCORING_FLOW_DIAGRAM.md**: Visual documentation:
  - Architecture diagram
  - Decision trees
  - API flow
  - Score progression examples

#### Code Examples
- Test script with 7 comprehensive scenarios
- Frontend integration snippets (JavaScript)
- API usage examples (curl, Python, JavaScript)

### Testing

#### Automated Tests
- `test_scoring_algorithm.py` includes:
  1. Progressive engagement scenario
  2. Quick bounce (negative signal)
  3. Dislike scenario
  4. Multiple search appearances
  5. One-shot calculation
  6. Watch time variations
  7. Like override behavior

#### Manual Testing
- All endpoints tested with curl
- Score progression verified
- Edge cases validated (negative scores, overflow)
- Batch updates tested with multiple places

### Use Cases

#### For Recommendation Systems
1. **Collaborative Filtering**
   - Use scores >= 7.0 as positive interactions
   - Use scores <= 3.0 as negative interactions
   - Direct input for matrix factorization

2. **Content-Based Filtering**
   - Extract themes from high-scoring places
   - Boost similar places in results

3. **Hybrid Approach** (Currently implemented)
   - Combines rating history with search intent
   - Filters out low-scoring places
   - Personalizes recommendations

### Migration Notes

#### For Existing Data
Old scoring system used different scale:
- Like: 5.0 → New: 10.0
- View: 3.0 → New: 5.0
- Click: 1.0 → New: 1.0
- Dislike: -1.0 → New: 1.0

Migration SQL available in `SCORING_ALGORITHM.md`

#### For Frontend Integration
1. **No Breaking Changes**: Existing endpoints still work
2. **New Endpoints**: Opt-in to new features
3. **Backward Compatible**: Old interaction types supported

### Future Enhancements

#### Planned Features (Not in this release)
- Time decay for old scores
- Context-aware scoring (time of day, season)
- Social signals (similar users)
- A/B testing framework
- Personalized scoring weights per user segment

#### Potential Improvements
- Real-time score updates via WebSockets
- Score analytics dashboard
- Machine learning model integration
- Cross-device tracking
- Offline support with sync

### Breaking Changes
- None - Fully backward compatible

### Deprecations
- `calculate_interest_score()` marked deprecated (still functional)
- Consider migrating to new scoring functions

### Known Issues
- None reported

### Dependencies
- No new dependencies added
- Uses existing: FastAPI, SQLModel, Python 3.8+

### Contributors
- Implementation: GitHub Copilot
- Date: December 11, 2025

### References
- Database Schema: `backend/app/schemas.py`
- Service Functions: `backend/app/services/scoring_service.py`
- API Endpoints: `backend/app/routers/rating.py`
- Auto-tracking: `backend/app/routers/recommendation.py`

---

## How to Use This Release

### For Backend Developers
1. Read `SCORING_QUICK_REFERENCE.md`
2. Review updated code in `scoring_service.py` and `rating.py`
3. Run test script: `python -m app.services.test_scoring_algorithm`

### For Frontend Developers
1. Read `SCORING_QUICK_REFERENCE.md`
2. Implement click tracking (see examples)
3. Implement watch time tracking (see examples)
4. Add like/dislike buttons (see examples)
5. Search tracking is automatic - no code needed!

### For Data Scientists
1. Read `SCORING_ALGORITHM.md` section on ML use cases
2. Use scores for collaborative filtering
3. Filter high-quality ratings (score >= 7.0)
4. Consider score velocity in models

### For Product Managers
1. Read `IMPLEMENTATION_SUMMARY.md`
2. Review example flows and use cases
3. Plan frontend integration timeline
4. Review performance implications

---

## Support & Documentation

- 📖 Full Docs: `backend/SCORING_ALGORITHM.md`
- ⚡ Quick Start: `backend/SCORING_QUICK_REFERENCE.md`
- 📊 Summary: `backend/IMPLEMENTATION_SUMMARY.md`
- 🎨 Diagrams: `backend/SCORING_FLOW_DIAGRAM.md`
- 🧪 Tests: `backend/app/services/test_scoring_algorithm.py`

## Version History

- **1.0.0** (2025-12-11) - Initial release of scoring algorithm
