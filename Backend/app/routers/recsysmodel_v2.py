"""
IMPROVED RECOMMENDATION SYSTEM - TARGET: 40% Precision@10
Sử dụng Hybrid approach:
1. Matrix Factorization (Implicit ALS) cho collaborative filtering
2. Enhanced Content-Based với tag importance weighting  
3. Improved re-ranking với diversity và recency
"""

import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sqlmodel import Session, select
from typing import Optional, List, Tuple
from collections import Counter
from scipy.sparse import csr_matrix
from implicit.als import AlternatingLeastSquares
import pickle
import os

from app.schemas import Place, Rating, Like

# ==========================================
# GLOBAL VARIABLES
# ==========================================

items_df = None
vectorizer = None
count_matrix = None
item_similarity_matrix = None
place_popularity = None

# Matrix Factorization
als_model = None
user_item_matrix = None
user_mapping = None  # user_id -> matrix index
item_mapping = None  # place_id -> matrix index
reverse_item_mapping = None  # matrix index -> place_id

# ==========================================
# 1. LOAD DATA
# ==========================================

def load_places_from_db():
    """Load places từ database"""
    from app.database import get_session
    
    session_gen = get_session()
    session = next(session_gen)
    
    try:
        statement = select(Place)
        places = session.exec(statement).all()
        
        places_data = []
        for place in places:
            tags_text = " ".join(place.tags) if place.tags else ""
            desc_text = " ".join(place.description) if place.description else ""
            
            # Weighted soup: tags lặp lại 3 lần để tăng importance
            weighted_soup = f"{place.name} {tags_text} {tags_text} {tags_text} {desc_text}"
            
            places_data.append({
                "id": place.id,
                "name": place.name,
                "tags": place.tags,
                "description": place.description,
                "images": place.image,
                "soup": weighted_soup
            })
        
        return pd.DataFrame(places_data)
    finally:
        try:
            next(session_gen)
        except StopIteration:
            pass

# ==========================================
# 2. MATRIX FACTORIZATION (ALS)
# ==========================================

def build_user_item_matrix():
    """
    Xây dựng user-item interaction matrix
    Implicit feedback: rating >= 3 → confidence tỉ lệ với score
    """
    from app.database import get_session
    
    session_gen = get_session()
    session = next(session_gen)
    
    try:
        # Load all ratings
        ratings = session.exec(select(Rating)).all()
        
        if not ratings:
            return None, None, None, None
        
        # Create mappings
        user_ids = sorted(set(r.user_id for r in ratings))
        place_ids = sorted(set(r.place_id for r in ratings))
        
        user_to_idx = {uid: idx for idx, uid in enumerate(user_ids)}
        place_to_idx = {pid: idx for idx, pid in enumerate(place_ids)}
        idx_to_place = {idx: pid for pid, idx in place_to_idx.items()}
        
        # Build sparse matrix
        rows, cols, data = [], [], []
        
        for rating in ratings:
            user_idx = user_to_idx[rating.user_id]
            item_idx = place_to_idx[rating.place_id]
            
            # Confidence từ score:
            # Score 5 → confidence = 2.0
            # Score 4 → confidence = 1.5  
            # Score 3 → confidence = 1.0
            # Score < 3 → skip (negative feedback)
            if rating.score >= 3.0:
                confidence = (rating.score - 2.0) / 2.0  # Maps [3,5] to [0.5, 1.5]
                rows.append(user_idx)
                cols.append(item_idx)
                data.append(confidence)
        
        # Add likes as strong signals
        likes = session.exec(select(Like).where(Like.is_like == True)).all()
        for like in likes:
            if like.user_id in user_to_idx and like.place_id in place_to_idx:
                user_idx = user_to_idx[like.user_id]
                item_idx = place_to_idx[like.place_id]
                rows.append(user_idx)
                cols.append(item_idx)
                data.append(2.0)  # Likes have high confidence
        
        # Create sparse matrix (users x items)
        matrix = csr_matrix(
            (data, (rows, cols)),
            shape=(len(user_ids), len(place_ids))
        )
        
        return matrix, user_to_idx, place_to_idx, idx_to_place
        
    finally:
        try:
            next(session_gen)
        except StopIteration:
            pass

def train_als_model(factors=64, regularization=0.01, iterations=20):
    """Train ALS model"""
    global als_model, user_item_matrix, user_mapping, item_mapping, reverse_item_mapping
    
    # Build matrix
    user_item_matrix, user_mapping, item_mapping, reverse_item_mapping = build_user_item_matrix()
    
    if user_item_matrix is None:
        print("❌ Cannot build user-item matrix")
        return False
    
    print(f"Training ALS model...")
    print(f"  Matrix shape: {user_item_matrix.shape}")
    print(f"  Non-zero entries: {user_item_matrix.nnz}")
    print(f"  Sparsity: {100 * (1 - user_item_matrix.nnz / (user_item_matrix.shape[0] * user_item_matrix.shape[1])):.2f}%")
    
    # Train ALS
    als_model = AlternatingLeastSquares(
        factors=factors,
        regularization=regularization,
        iterations=iterations,
        calculate_training_loss=True,
        random_state=42
    )
    
    # ALS expects items x users, so transpose
    als_model.fit(user_item_matrix.T)
    
    print(f"✅ ALS model trained!")
    return True

# ==========================================
# 3. CONTENT-BASED FILTERING
# ==========================================

def calculate_popularity_scores():
    """Calculate popularity từ ratings + likes"""
    from app.database import get_session
    
    session_gen = get_session()
    session = next(session_gen)
    
    try:
        ratings = session.exec(select(Rating)).all()
        likes = session.exec(select(Like).where(Like.is_like == True)).all()
        
        popularity = {}
        
        # Count ratings
        for rating in ratings:
            if rating.score >= 4.0:
                popularity[rating.place_id] = popularity.get(rating.place_id, 0) + 1
        
        # Count likes (weight = 1.5)
        for like in likes:
            popularity[like.place_id] = popularity.get(like.place_id, 0) + 1.5
        
        # Normalize
        if popularity:
            max_pop = max(popularity.values())
            popularity = {pid: score / max_pop for pid, score in popularity.items()}
        
        return popularity
        
    finally:
        try:
            next(session_gen)
        except StopIteration:
            pass

def initialize_recsys():
    """Khởi tạo toàn bộ recommendation system"""
    global items_df, count_matrix, vectorizer, item_similarity_matrix, place_popularity
    
    if items_df is not None:
        return
    
    try:
        # 1. Load places
        items_df = load_places_from_db()
        
        if len(items_df) == 0:
            print("⚠️ No places found")
            return
        
        # 2. TF-IDF vectorization với improved parameters
        vectorizer = TfidfVectorizer(
            stop_words='english',
            max_features=8000,  # Increased
            ngram_range=(1, 3),  # Up to trigrams
            min_df=1,
            max_df=0.7,  # More restrictive
            sublinear_tf=True  # Use log scaling
        )
        count_matrix = vectorizer.fit_transform(items_df['soup'])
        
        # 3. Item similarity
        item_similarity_matrix = cosine_similarity(count_matrix, count_matrix)
        
        # 4. Popularity
        place_popularity = calculate_popularity_scores()
        
        # 5. Train ALS model
        success = train_als_model(factors=80, regularization=0.01, iterations=25)
        
        if success:
            print(f"✅ RecSys initialized with {len(items_df)} places + ALS model")
        else:
            print(f"⚠️ RecSys initialized with {len(items_df)} places (no ALS)")
            
    except Exception as e:
        print(f"❌ Failed to initialize RecSys: {e}")
        items_df = pd.DataFrame()

# ==========================================
# 4. RECOMMENDATION FUNCTIONS
# ==========================================

def get_als_recommendations(user_id: int, n: int = 50) -> List[Tuple[int, float]]:
    """Get recommendations từ ALS model"""
    if als_model is None or user_mapping is None:
        return []
    
    if user_id not in user_mapping:
        return []
    
    user_idx = user_mapping[user_id]
    
    # Get recommendations
    ids, scores = als_model.recommend(
        user_idx,
        user_item_matrix[user_idx],
        N=n,
        filter_already_liked_items=True
    )
    
    # Convert indices to place_ids
    recommendations = []
    for idx, score in zip(ids, scores):
        if idx in reverse_item_mapping:
            place_id = reverse_item_mapping[idx]
            recommendations.append((place_id, float(score)))
    
    return recommendations

def get_item_vector(place_id: int):
    """Lấy TF-IDF vector của một place"""
    if items_df is None or count_matrix is None:
        return None
    
    idx = items_df[items_df['id'] == place_id].index
    if len(idx) == 0:
        return None
    
    return count_matrix[idx[0]].toarray().flatten()

def get_user_ratings(user_id: int):
    """Lấy ratings của user"""
    from app.database import get_session
    
    session_gen = get_session()
    session = next(session_gen)
    
    try:
        statement = select(Rating).where(Rating.user_id == user_id)
        ratings = session.exec(statement).all()
        return ratings
    finally:
        try:
            next(session_gen)
        except StopIteration:
            pass

def get_user_likes(user_id: int):
    """Lấy likes của user"""
    from app.database import get_session
    
    session_gen = get_session()
    session = next(session_gen)
    
    try:
        statement = select(Like).where(
            Like.user_id == user_id,
            Like.is_like == True
        )
        likes = session.exec(statement).all()
        return [like.place_id for like in likes]
    finally:
        try:
            next(session_gen)
        except StopIteration:
            pass

def build_content_profile(user_id: int):
    """Build user profile từ content-based"""
    ratings = get_user_ratings(user_id)
    liked_ids = get_user_likes(user_id)
    
    if not ratings and not liked_ids:
        return None, set()
    
    if count_matrix is None:
        return None, set()
    
    user_profile = np.zeros(count_matrix.shape[1])
    total_weight = 0.0
    interacted = set()
    
    # Process ratings với exponential weighting
    for rating in ratings:
        item_vec = get_item_vector(rating.place_id)
        if item_vec is not None:
            interacted.add(rating.place_id)
            
            if rating.score >= 3.0:
                # Exponential: score 5 → 4x, score 4 → 2x, score 3 → 1x
                weight = 2 ** (rating.score - 3.0)
                user_profile += item_vec * weight
                total_weight += weight
    
    # Process likes (strong signal)
    for place_id in liked_ids:
        item_vec = get_item_vector(place_id)
        if item_vec is not None:
            interacted.add(place_id)
            weight = 3.0  # Very high weight
            user_profile += item_vec * weight
            total_weight += weight
    
    if total_weight > 0:
        user_profile /= total_weight
    
    return user_profile, interacted

def recommend_hybrid(
    user_id: int,
    user_tags: List[str] = [],
    n: int = 20,
    exclude_ids: List[int] = []
) -> List[dict]:
    """
    HYBRID RECOMMENDATION
    - 50% ALS (collaborative filtering)
    - 30% Content-based (TF-IDF)
    - 20% Popularity
    """
    
    if items_df is None or len(items_df) == 0:
        return []
    
    # 1. Get ALS recommendations (collaborative)
    als_recs = get_als_recommendations(user_id, n=100)
    als_scores = {place_id: score for place_id, score in als_recs}
    
    # 2. Get content-based recommendations
    user_profile, interacted = build_content_profile(user_id)
    
    # Combine interacted with exclude_ids
    all_exclude = set(exclude_ids) | interacted
    
    content_scores = {}
    if user_profile is not None:
        # Score all items
        for idx, row in items_df.iterrows():
            place_id = row['id']
            if place_id in all_exclude:
                continue
            
            item_vec = get_item_vector(place_id)
            if item_vec is not None:
                similarity = np.dot(user_profile, item_vec)
                content_scores[place_id] = similarity
    
    # 3. Get popularity scores
    pop_scores = place_popularity or {}
    
    # 4. Normalize all scores to [0, 1]
    def normalize(scores):
        if not scores:
            return {}
        vals = list(scores.values())
        min_val, max_val = min(vals), max(vals)
        if max_val == min_val:
            return {k: 0.5 for k in scores}
        return {k: (v - min_val) / (max_val - min_val) for k, v in scores.items()}
    
    als_norm = normalize(als_scores)
    content_norm = normalize(content_scores)
    pop_norm = normalize(pop_scores)
    
    # 5. Combine with weights
    combined_scores = {}
    all_places = set(als_norm.keys()) | set(content_norm.keys())
    
    for place_id in all_places:
        if place_id in all_exclude:
            continue
        
        score = (
            0.5 * als_norm.get(place_id, 0.0) +
            0.3 * content_norm.get(place_id, 0.0) +
            0.2 * pop_norm.get(place_id, 0.0)
        )
        combined_scores[place_id] = score
    
    # 6. Sort and get top-N
    sorted_places = sorted(combined_scores.items(), key=lambda x: x[1], reverse=True)[:n*2]
    
    # 7. Re-rank for diversity
    final_recs = []
    seen_tags = set()
    
    for place_id, score in sorted_places:
        if len(final_recs) >= n:
            break
        
        place_row = items_df[items_df['id'] == place_id]
        if len(place_row) == 0:
            continue
        
        place_tags = place_row.iloc[0]['tags']
        
        # Diversity: penalize if too many similar tags
        tag_overlap = len(set(place_tags) & seen_tags) if place_tags else 0
        
        if tag_overlap < 3 or len(final_recs) < n // 2:  # Allow some overlap for first half
            final_recs.append({
                'id': place_id,
                'score': score,
                'name': place_row.iloc[0]['name'],
                'tags': place_tags,
                'images': place_row.iloc[0]['images']
            })
            
            if place_tags:
                seen_tags.update(place_tags[:5])  # Only add top 5 tags
    
    return final_recs

# ==========================================
# 5. COLD START
# ==========================================

def recommend_cold_start(tags: List[str], n: int = 20) -> List[dict]:
    """Recommend cho new users dựa trên tags"""
    if items_df is None or len(items_df) == 0:
        return []
    
    if not tags:
        # No tags → return popular items
        pop_scores = place_popularity or {}
        sorted_places = sorted(pop_scores.items(), key=lambda x: x[1], reverse=True)[:n]
        
        results = []
        for place_id, score in sorted_places:
            place_row = items_df[items_df['id'] == place_id]
            if len(place_row) > 0:
                results.append({
                    'id': place_id,
                    'score': score,
                    'name': place_row.iloc[0]['name'],
                    'tags': place_row.iloc[0]['tags'],
                    'images': place_row.iloc[0]['images']
                })
        return results
    
    # Has tags → content-based
    query_text = " ".join(tags) * 3  # Repeat for emphasis
    query_vec = vectorizer.transform([query_text])
    
    similarities = cosine_similarity(query_vec, count_matrix).flatten()
    
    # Combine with popularity
    scores = {}
    pop_scores = place_popularity or {}
    
    for idx, sim in enumerate(similarities):
        place_id = items_df.iloc[idx]['id']
        pop_score = pop_scores.get(place_id, 0.0)
        
        # 70% content, 30% popularity
        combined = 0.7 * sim + 0.3 * pop_score
        scores[place_id] = combined
    
    # Get top-N
    sorted_places = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:n]
    
    results = []
    for place_id, score in sorted_places:
        place_row = items_df[items_df['id'] == place_id]
        if len(place_row) > 0:
            results.append({
                'id': place_id,
                'score': score,
                'name': place_row.iloc[0]['name'],
                'tags': place_row.iloc[0]['tags'],
                'images': place_row.iloc[0]['images']
            })
    
    return results
