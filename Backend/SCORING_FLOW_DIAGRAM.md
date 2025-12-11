```mermaid
# User-Place Scoring Algorithm Flow

## Overall Architecture

                                    ┌─────────────────────────┐
                                    │   Frontend (React/JS)   │
                                    └───────────┬─────────────┘
                                                │
                    ┌───────────────────────────┼───────────────────────────┐
                    │                           │                           │
                    ▼                           ▼                           ▼
        ┌─────────────────────┐    ┌─────────────────────┐    ┌─────────────────────┐
        │  /recommend         │    │  /rating/interact   │    │  /rating/watch-time │
        │  (Search)           │    │  (Click/Like)       │    │  (View Duration)    │
        └──────────┬──────────┘    └──────────┬──────────┘    └──────────┬──────────┘
                   │                           │                           │
                   │    ┌──────────────────────┼───────────────────────────┘
                   │    │                      │
                   ▼    ▼                      ▼
            ┌──────────────────────────────────────────┐
            │     scoring_service.py Functions         │
            │  ┌────────────────────────────────────┐  │
            │  │ update_score_on_search_similarity  │  │ +0.5
            │  │ update_score_on_click              │  │ +1.0
            │  │ update_score_on_like               │  │ →10.0
            │  │ update_score_on_dislike            │  │ →1.0
            │  │ update_score_on_watch_time         │  │ -2/+1/+2
            │  └────────────────────────────────────┘  │
            └──────────────────┬───────────────────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │   Rating Table      │
                    │  ┌───────────────┐  │
                    │  │ user_id       │  │
                    │  │ place_id      │  │
                    │  │ score (0-10)  │  │
                    │  └───────────────┘  │
                    └─────────────────────┘

## Scoring Decision Tree

    User Interaction
          │
          ├─── Like? ────────────────────────────────► Score = 10.0 (MAX)
          │
          ├─── Dislike? ─────────────────────────────► Score = 1.0 (MIN)
          │
          ├─── Search Appear? ───────────────────────► Score += 0.5
          │
          ├─── Click? ───────────────────────────────► Score += 1.0
          │
          └─── Watch Time?
                   │
                   ├─── < 10 seconds ─────────────────► Score -= 2.0
                   │
                   ├─── 10-60 seconds ────────────────► Score += 1.0
                   │
                   └─── > 60 seconds ─────────────────► Score += 2.0
                                │
                                ▼
                         Clamp to [0.0, 10.0]

## Score Progression Example

    Time    │ Event                │ Calculation        │ Score
    ────────┼──────────────────────┼────────────────────┼──────
    T0      │ Initial              │ -                  │ 0.0
    T1      │ Search appears       │ 0.0 + 0.5          │ 0.5
    T2      │ User clicks          │ 0.5 + 1.0          │ 1.5
    T3      │ Views 5s (bounce)    │ 1.5 - 2.0 → 0.0    │ 0.0
    T4      │ Search appears again │ 0.0 + 0.5          │ 0.5
    T5      │ User clicks again    │ 0.5 + 1.0          │ 1.5
    T6      │ Views 45s            │ 1.5 + 1.0          │ 2.5
    T7      │ User likes           │ → 10.0             │ 10.0

## API Flow Diagram

    Frontend                 Backend                 Database
       │                        │                        │
       │  POST /recommend       │                        │
       ├───────────────────────►│                        │
       │                        │  Get recommendations   │
       │                        ├───────────────────────►│
       │                        │◄───────────────────────┤
       │                        │  For each place:       │
       │                        │  Update score +0.5     │
       │                        ├───────────────────────►│
       │◄───────────────────────┤                        │
       │  [Places returned]     │                        │
       │                        │                        │
       │  User clicks place     │                        │
       │  POST /interact        │                        │
       ├───────────────────────►│                        │
       │                        │  Update score +1.0     │
       │                        ├───────────────────────►│
       │◄───────────────────────┤                        │
       │  {score: 1.5}          │                        │
       │                        │                        │
       │  Every 10s while view  │                        │
       │  POST /watch-time      │                        │
       ├───────────────────────►│                        │
       │                        │  Update based on time  │
       │                        ├───────────────────────►│
       │◄───────────────────────┤                        │
       │  {score: 2.5}          │                        │
       │                        │                        │
       │  User clicks like      │                        │
       │  POST /interact        │                        │
       ├───────────────────────►│                        │
       │                        │  Set score = 10.0      │
       │                        ├───────────────────────►│
       │◄───────────────────────┤                        │
       │  {score: 10.0}         │                        │

## Interaction Priority

    Priority 1 (Overrides Everything)
    ┌────────────────────────────┐
    │  Like → Score = 10.0       │
    │  Dislike → Score = 1.0     │
    └────────────────────────────┘
                 │
                 ▼
    Priority 2 (Cumulative)
    ┌────────────────────────────┐
    │  Search Appear: +0.5       │
    │  Click: +1.0               │
    │  Watch Time: -2/+1/+2      │
    └────────────────────────────┘
                 │
                 ▼
    ┌────────────────────────────┐
    │  Clamp to [0.0, 10.0]      │
    └────────────────────────────┘

## Watch Time Thresholds

    Time Spent │ Score Change │ Interpretation
    ───────────┼──────────────┼────────────────────
    0-9s       │  -2.0        │ Not interested
               │              │ Quick bounce
    ───────────┼──────────────┼────────────────────
    10-60s     │  +1.0        │ Basic interest
               │              │ Read description
    ───────────┼──────────────┼────────────────────
    61s+       │  +2.0        │ Strong interest
               │              │ Thorough review
    ───────────┴──────────────┴────────────────────

## Database Queries

    # Get user's rating for a place
    SELECT score FROM rating 
    WHERE user_id = ? AND place_id = ?

    # Update existing rating
    UPDATE rating 
    SET score = ? 
    WHERE user_id = ? AND place_id = ?

    # Create new rating
    INSERT INTO rating (user_id, place_id, score) 
    VALUES (?, ?, ?)

    # Get all user's highly-rated places (for recommendations)
    SELECT place_id, score FROM rating 
    WHERE user_id = ? AND score >= 7.0
    ORDER BY score DESC

## Frontend Integration Points

    1. Page Load (Place Detail)
       └─► Start watch timer
       
    2. Click (Place Card/Link)
       └─► POST /rating/interact {interaction_type: "click"}
       
    3. Every 10 seconds (While viewing)
       └─► POST /rating/watch-time {watch_time_seconds: N}
       
    4. Like Button Click
       └─► POST /rating/interact {interaction_type: "like"}
       
    5. Dislike Button Click
       └─► POST /rating/interact {interaction_type: "dislike"}
       
    6. Search/Recommend
       └─► Backend automatically handles +0.5 per result

## Score Clamping Examples

    Calculation │ Raw Result │ Clamped Result
    ────────────┼────────────┼────────────────
    1.5 - 2.0   │  -0.5      │  0.0 (min)
    8.0 + 3.0   │  11.0      │ 10.0 (max)
    5.0 + 1.0   │   6.0      │  6.0 (within)
    0.0 - 2.0   │  -2.0      │  0.0 (min)
```
