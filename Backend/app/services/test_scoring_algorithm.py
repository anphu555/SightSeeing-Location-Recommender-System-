"""
Test and demonstration script for the user-place scoring algorithm.
This script shows how scores change based on different user interactions.
"""

from app.services.scoring_service import (
    calculate_user_place_score,
    update_score_on_search_similarity,
    update_score_on_like,
    update_score_on_dislike,
    update_score_on_watch_time
)


def test_scoring_scenarios():
    """Test various scoring scenarios"""
    
    print("=" * 80)
    print("USER-PLACE SCORING ALGORITHM TEST")
    print("=" * 80)
    
    # Scenario 1: Progressive engagement
    print("\n📊 SCENARIO 1: Progressive Engagement")
    print("-" * 80)
    score = 0.0
    print(f"Initial score: {score}")
    
    # Place appears in search
    score = update_score_on_search_similarity(score)
    print(f"After appearing in search (+0.5): {score}")
    
    # User views for 45 seconds
    score = update_score_on_watch_time(score, 45)
    print(f"After 45s viewing (+1.0): {score}")
    
    # Appears in another search
    score = update_score_on_search_similarity(score)
    print(f"After appearing in another search (+0.5): {score}")
    
    # User views for 90 seconds
    score = update_score_on_watch_time(score, 90)
    print(f"After 90s viewing (+2.0): {score}")
    
    # User likes
    score = update_score_on_like(score)
    print(f"After user LIKE (→10.0): {score}")
    
    # Scenario 2: Quick bounce (negative signal)
    print("\n📊 SCENARIO 2: Quick Bounce (Negative Signal)")
    print("-" * 80)
    score = 0.0
    print(f"Initial score: {score}")
    
    score = update_score_on_watch_time(score, 5)  # Quick bounce
    print(f"After 5s viewing (-2.0, clamped to 0.0): {score}")
    
    # Scenario 3: Dislike
    print("\n📊 SCENARIO 3: User Dislikes Place")
    print("-" * 80)
    score = 0.0
    print(f"Initial score: {score}")
    
    score = update_score_on_search_similarity(score)
    print(f"After appearing in search (+0.5): {score}")
    
    score = update_score_on_dislike(score)
    print(f"After user DISLIKE (→1.0): {score}")
    
    # Scenario 4: Multiple searches (discovery pattern)
    print("\n📊 SCENARIO 4: Multiple Search Appearances")
    print("-" * 80)
    score = 0.0
    print(f"Initial score: {score}")
    
    for i in range(1, 6):
        score = update_score_on_search_similarity(score)
        print(f"After search #{i} (+0.5): {score}")
    
    # Scenario 5: Using calculate_user_place_score (one-shot calculation)
    print("\n📊 SCENARIO 5: One-shot Score Calculation")
    print("-" * 80)
    
    score = calculate_user_place_score(
        search_similarity=3,  # Appeared in 3 searches
        like=False,
        dislike=False,
        watch_time_seconds=45  # Viewed for 45 seconds
    )
    print(f"3 searches + 45s view = {score}")
    print(f"Breakdown: (3 × 0.5) + (1.0 for moderate time) = {score}")
    
    # Scenario 6: Watch time variations
    print("\n📊 SCENARIO 6: Watch Time Variations")
    print("-" * 80)
    
    base_score = 5.0
    print(f"Base score: {base_score}")
    
    quick = update_score_on_watch_time(base_score, 5)
    print(f"Quick bounce (5s, -2.0): {quick}")
    
    moderate = update_score_on_watch_time(base_score, 30)
    print(f"Moderate time (30s, +1.0): {moderate}")
    
    extended = update_score_on_watch_time(base_score, 120)
    print(f"Extended time (120s, +2.0): {extended}")
    
    # Scenario 7: Like overrides everything
    print("\n📊 SCENARIO 7: Like Overrides All Previous Scores")
    print("-" * 80)
    
    score = 0.0
    print(f"Initial score: {score}")
    
    score = update_score_on_search_similarity(score)
    score = update_score_on_watch_time(score, 5)  # Quick bounce
    print(f"After search and quick bounce: {score}")
    
    score = update_score_on_like(score)
    print(f"After LIKE (overrides to 10.0): {score}")
    
    # Summary table
    print("\n" + "=" * 80)
    print("SCORING RULES SUMMARY")
    print("=" * 80)
    print(f"{'Interaction':<25} {'Score Change':<20} {'Description':<35}")
    print("-" * 80)
    print(f"{'Search Appear':<25} {'+0.5 per appear':<20} {'Place in similar search results':<35}")
    print(f"{'Like':<25} {'→ 10.0 (max)':<20} {'User explicitly liked place':<35}")
    print(f"{'Dislike':<25} {'→ 1.0 (min)':<20} {'User explicitly disliked place':<35}")
    print(f"{'Watch < 10s':<25} {'-2.0':<20} {'Quick bounce, not interested':<35}")
    print(f"{'Watch 10-60s':<25} {'+1.0':<20} {'Moderate engagement':<35}")
    print(f"{'Watch > 60s':<25} {'+2.0':<20} {'Strong engagement':<35}")
    print("=" * 80)


if __name__ == "__main__":
    test_scoring_scenarios()
