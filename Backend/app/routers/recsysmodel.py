import pandas as pd
import numpy as np
from lightfm import LightFM
from lightfm.data import Dataset

# 1. Your Database
# Có lẽ sẽ dùng pandas đọc file CSV thay vì đống này
items_df = pd.DataFrame([
    {"id": 0, "name": "Lầu Ông Hoàng", "kind": "castle", "province": "Bình Thuận", "climate": "warm"},
    {"id": 1, "name": "Tháp Po Sah Inư", "kind": "ruins", "province": "Bình Thuận", "climate": "warm"},
    {"id": 2, "name": "Vịnh Hạ Long", "kind": "island", "province": "Quảng Ninh", "climate": "cool"},
])

# 2. Initialize LightFM Dataset
# We need to tell LightFM all possible features (kinds, climates, etc.)
dataset = Dataset()
dataset.fit(
    users=[0], # Dummy user
    items=items_df['id'],
    user_features=['wants_castle', 'wants_ruins', 'wants_island', 'wants_warm', 'wants_cool'],
    item_features=['is_castle', 'is_ruins', 'is_island', 'is_warm', 'is_cool']
)

# 3. Build Item Features Matrix
# Map: kind="castle" -> feature="is_castle"
def build_item_features(row):
    features = [f"is_{row['kind']}", f"is_{row['climate']}"]
    return (row['id'], features)

item_features = dataset.build_item_features(
    (row['id'], [f"is_{row['kind']}", f"is_{row['climate']}"]) 
    for index, row in items_df.iterrows()
)

# --- NOTE: In a real app, you would TRAIN the model here using past interaction data. ---
# Since you have no data yet, we will initialize a model with random weights 
# (or manual weights if you are advanced).
model = LightFM(loss='warp')
# model.fit(interactions, user_features=..., item_features=..., epochs=30)



# ==============================\
# Step 2
def recommend(user_prompt):
    # --- PHASE 1: HARD FILTERING (The "Filter" Part) ---
    # Only keep items in the requested province
    candidates = items_df[items_df['province'].isin(user_prompt['location'])]
    
    if candidates.empty:
        return []

    # --- PHASE 2: CONSTRUCT USER REPRESENTATION (The "Cold Start" Trick) ---
    # Convert user prompt into LightFM user features
    active_features = []
    
    if user_prompt['type'] != 'unknown':
        active_features.append(f"wants_{user_prompt['type']}") # e.g., 'wants_island'
    
    # Simple logic to map weather preference
    if user_prompt['weather'] == 'cool':
        active_features.append("wants_cool")
    elif user_prompt['weather'] == 'warm':
        active_features.append("wants_warm")

    # Build the sparse matrix for this specific request
    # We use a dummy user_id=0, but the 'features' are what matter
    user_features_matrix = dataset.build_user_features([(0, active_features)])

    # --- PHASE 3: RANKING (The LightFM Part) ---
    candidate_ids = candidates['id'].values
    
    # Predict scores for ONLY the filtered candidates
    # 'predict' calculates the dot product between User Features and Candidate Item Features
    scores = model.predict(
        user_ids=0, 
        item_ids=candidate_ids, 
        user_features=user_features_matrix, 
        item_features=item_features
    )

    # Attach scores to the candidates
    candidates = candidates.copy() # Avoid warning
    candidates['lightfm_score'] = scores
    
    # Sort descending
    return candidates.sort_values(by='lightfm_score', ascending=False)

# --- TEST IT ---
user_request = {
    "location": ["Quảng Ninh"],
    "type": "island",
    "weather": "unknown"
}

results = recommend(user_request)
print(results[['name', 'kind', 'lightfm_score']])
