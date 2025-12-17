# Rating Algorithm Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         USER INTERACTIONS                               │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    ▼               ▼               ▼
            ┌──────────────┐ ┌───────────┐ ┌──────────────┐
            │  View Time   │ │   Like/   │ │   Comment    │
            │  (seconds)   │ │  Dislike  │ │              │
            └──────────────┘ └───────────┘ └──────────────┘
                    │               │               │
                    ▼               ▼               ▼
            ┌──────────────┐ ┌───────────┐ ┌──────────────┐
            │  < 5 sec?    │ │  is_like? │ │  First time? │
            │  → IGNORE    │ │  True/    │ │  → +0.5      │
            │              │ │  False    │ │  → IGNORE    │
            │  5-120 sec?  │ │           │ │              │
            │  → 1.5-4.0   │ │  True:    │ │              │
            │              │ │  → +4     │ │              │
            │  > 120 sec?  │ │           │ │              │
            │  → 4.0       │ │  False:   │ │              │
            │              │ │  → -5     │ │              │
            │  Existing?   │ │  (min 1)  │ │              │
            │  → SKIP      │ │           │ │              │
            └──────────────┘ └───────────┘ └──────────────┘
                    │               │               │
                    └───────────────┼───────────────┘
                                    ▼
                        ┌───────────────────────┐
                        │   Calculate Score     │
                        │   (RatingScorer)      │
                        └───────────────────────┘
                                    │
                                    ▼
                        ┌───────────────────────┐
                        │   Clamp to [1.0, 5.0] │
                        └───────────────────────┘
                                    │
                                    ▼
                        ┌───────────────────────┐
                        │   Update Database     │
                        │   (rating table)      │
                        └───────────────────────┘
                                    │
                                    ▼
                        ┌───────────────────────┐
                        │   Return Response     │
                        └───────────────────────┘
```

## Formula Details

### View Time Score Calculation

```
if view_time < 5:
    return None  # Ignore

if view_time >= 120:
    return 4.0

# Linear interpolation
time_range = 120 - 5 = 115
score_range = 4.0 - 1.5 = 2.5
score = 1.5 + ((view_time - 5) / 115) * 2.5
```

### Score Update Logic

```python
# Start with existing score or 0
current_score = existing_rating.score if exists else 0.0

# 1. View time (only if no existing rating)
if view_time and not exists:
    current_score = calculate_view_time_score(view_time)

# 2. Like/Dislike
if is_like == True:
    current_score += 4.0
elif is_like == False:
    current_score -= 5.0
    current_score = max(current_score, 1.0)

# 3. Comment (only first time)
if has_commented and comment_count == 1:
    current_score += 0.5

# 4. Clamp to valid range
final_score = max(1.0, min(current_score, 5.0))
```

## Data Flow

```
Frontend                Backend                      Database
   │                       │                            │
   │   POST /rating/      │                            │
   │   view-time          │                            │
   ├──────────────────────>│                            │
   │                       │  SELECT rating WHERE      │
   │                       │  user_id & place_id       │
   │                       ├───────────────────────────>│
   │                       │<───────────────────────────┤
   │                       │  existing_rating or None   │
   │                       │                            │
   │                       │  Calculate new score       │
   │                       │  using RatingScorer        │
   │                       │                            │
   │                       │  UPDATE or INSERT rating   │
   │                       ├───────────────────────────>│
   │                       │<───────────────────────────┤
   │                       │  Commit success            │
   │<──────────────────────┤                            │
   │   Response:           │                            │
   │   {score: 2.59}       │                            │
```

## Integration Points

```
┌─────────────────────────────────────────────────────────────┐
│                     FRONTEND INTEGRATION                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. Place Detail Page Load:                                │
│     const startTime = Date.now()                           │
│                                                             │
│  2. User Interactions:                                     │
│     - Like button → POST /likes/place                     │
│     - Dislike button → POST /likes/place                  │
│     - Comment form → POST /comments                       │
│                                                             │
│  3. Page Unload:                                          │
│     const viewTime = (Date.now() - startTime) / 1000      │
│     POST /rating/view-time {view_time_seconds: viewTime}  │
│                                                             │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                     BACKEND INTEGRATION                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  All endpoints automatically call RatingScorer:            │
│                                                             │
│  rating.py: track_view_time()                             │
│    └─> RatingScorer.update_rating(view_time_seconds=X)    │
│                                                             │
│  like.py: like_dislike_place()                            │
│    └─> RatingScorer.update_rating(is_like=True/False)     │
│                                                             │
│  comment.py: create_comment()                             │
│    └─> RatingScorer.update_rating(has_commented=True)     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Example Score Progression

```
Time  Action          Current Score  Change      New Score   Note
────────────────────────────────────────────────────────────────
0s    Page loaded     0.0            -           0.0         
60s   View ended      0.0            +2.59       2.59        View time
61s   Comment         2.59           +0.5        3.09        First comment
62s   Like            3.09           +4.0        5.0         Max reached
63s   View again      5.0            0           5.0         Has rating, ignore
────────────────────────────────────────────────────────────────

Alternative flow:
────────────────────────────────────────────────────────────────
0s    Page loaded     0.0            -           0.0
3s    Quick exit      0.0            0           0.0         < 5s, ignored
10s   Retry page      0.0            -           0.0
20s   Dislike         0.0            -5+1.5      1.0         Min score
────────────────────────────────────────────────────────────────
```
