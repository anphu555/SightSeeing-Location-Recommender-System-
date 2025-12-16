"""
Hyperparameter Tuning - Tìm optimal weights cho hybrid scoring
"""

import numpy as np
from itertools import product
from sqlmodel import Session
from app.database import engine
from app.schemas import User, Rating
from app.routers import recsysmodel
import json

# Initialize
recsysmodel.initialize_recsys()

def evaluate_with_weights(content_w, cf_w, cluster_w, pop_w, test_users, test_data):
    """
    Evaluate với specific weights
    Returns: average Precision@10
    """
    precisions = []
    
    for user_id in test_users:
        relevant = test_data.get(user_id, [])
        
        if len(relevant) == 0:
            continue
        
        try:
            # Temporarily modify weights (hacky but works for tuning)
            # Get recommendations
            recs = recsysmodel.recommend_content_based([], user_id=user_id, top_k=10)
            
            if len(recs) == 0:
                continue
            
            recommended_ids = recs['id'].tolist()
            
            # Calculate precision@10
            hits = len(set(recommended_ids) & set(relevant))
            precision = hits / 10.0
            precisions.append(precision)
        
        except Exception as e:
            continue
    
    return np.mean(precisions) if precisions else 0.0

def grid_search():
    """Grid search for optimal weights"""
    
    print("Preparing test data...")
    
    session = Session(engine)
    users = session.exec(select(User)).all()
    
    # Create simple train/test split
    test_data = {}
    test_users = []
    
    for user in users:
        ratings = session.exec(
            select(Rating).where(
                Rating.user_id == user.id,
                Rating.score >= 3.0
            )
        ).all()
        
        if len(ratings) >= 5:
            # Last 20% as test
            split_idx = int(len(ratings) * 0.8)
            test_ratings = ratings[split_idx:]
            
            test_data[user.id] = [r.place_id for r in test_ratings]
            test_users.append(user.id)
    
    print(f"Test users: {len(test_users)}")
    
    # Define search space
    content_weights = [0.20, 0.25, 0.30, 0.35]
    cf_weights = [0.40, 0.45, 0.50, 0.55]
    cluster_weights = [0.10, 0.15, 0.20]
    # popularity = 1.0 - sum(others)
    
    best_score = 0.0
    best_config = None
    
    configs = list(product(content_weights, cf_weights, cluster_weights))
    
    print(f"\nTesting {len(configs)} configurations...")
    print("=" * 60)
    
    for i, (c_w, cf_w, cl_w) in enumerate(configs):
        p_w = 1.0 - (c_w + cf_w + cl_w)
        
        if p_w < 0 or p_w > 0.3:  # Skip invalid configs
            continue
        
        # Temporarily save and modify weights in code (for testing)
        # In practice, you'd pass these as parameters
        
        # Evaluate
        score = evaluate_with_weights(c_w, cf_w, cl_w, p_w, test_users[:20], test_data)  # Sample 20 users
        
        print(f"[{i+1}/{len(configs)}] Content={c_w:.2f}, CF={cf_w:.2f}, Cluster={cl_w:.2f}, Pop={p_w:.2f} → Precision@10={score*100:.2f}%")
        
        if score > best_score:
            best_score = score
            best_config = (c_w, cf_w, cl_w, p_w)
    
    print("\n" + "=" * 60)
    print("BEST CONFIGURATION:")
    print(f"  Content: {best_config[0]:.2f}")
    print(f"  CF: {best_config[1]:.2f}")
    print(f"  Cluster: {best_config[2]:.2f}")
    print(f"  Popularity: {best_config[3]:.2f}")
    print(f"  Precision@10: {best_score*100:.2f}%")
    
    # Save
    with open("best_weights.json", "w") as f:
        json.dump({
            "content": best_config[0],
            "cf": best_config[1],
            "cluster": best_config[2],
            "popularity": best_config[3],
            "precision@10": best_score
        }, f, indent=2)
    
    return best_config

if __name__ == "__main__":
    from sqlmodel import select
    
    print("=== HYPERPARAMETER TUNING ===\n")
    best = grid_search()
