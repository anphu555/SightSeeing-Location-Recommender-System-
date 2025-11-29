import cornac
from cornac.data import TextModality
from cornac.eval_methods import RatioSplit
from cornac.models import ConvMF, CTR

# --- STEP 1: LOAD YOUR DATA ---
# 1. Feedback Data: (User_ID, Item_ID, Rating)
# Represents visits or likes. If you only have "visited" (1) vs "not visited" (0), pass 1s.
feedback_data = [
    ('User1', 'Paris', 5),
    ('User1', 'London', 4),
    ('User2', 'Paris', 5),
    ('User2', 'Tokyo', 5),
    ('User3', 'London', 3),
    # ... load your actual database here
]

# 2. Text Data: (Item_ID, Description_String)
# The text descriptions for your destinations
item_text_data = [
    ('Paris', "The city of lights, romantic eiffel tower and museums"),
    ('London', "Big Ben, british museum, rain and history"),
    ('Tokyo', "Sushi, anime, shibuya crossing and temples"),
    # ... ensure every item in feedback_data has an entry here
]

# Separate IDs and Texts for Cornac
item_ids = [x[0] for x in item_text_data]
descriptions = [x[1] for x in item_text_data]

# --- STEP 2: CREATE TEXT MODALITY ---
# This tells Cornac how to handle the text. 
# 'corpus' is your list of strings, 'ids' maps them to items.
item_text_modality = TextModality(
    corpus=descriptions,
    ids=item_ids,
    tokenizer=None, # Default tokenizer splits by space; you can customize this
    max_vocab=5000, # Limit vocabulary size
    max_doc_freq=0.5 # Remove words that appear in >50% of docs (stopwords)
)

# --- STEP 3: CREATE DATASET & SPLIT ---
# RatioSplit automatically handles the training/testing split
rs = RatioSplit(
    data=feedback_data,
    test_size=0.2,
    item_text=item_text_modality, # <--- IMPORTANT: Inject text here
    verbose=True,
    seed=123
)

# --- STEP 4: DEFINE MODELS ---
# We will compare a standard baseline (MF) vs. a Text Model (ConvMF)
models = [
    # 1. Matrix Factorization (Baseline - ignores text)
    cornac.models.MF(k=10, max_iter=20, learning_rate=0.01, seed=123, name="Standard MF"),
    
    # 2. ConvMF (The "Best" Model - uses text)
    # Note: Requires TensorFlow. Adjust 'k' (latent factors) and 'n_epochs' as needed.
    cornac.models.ConvMF(k=10, n_epochs=5, verbose=True, seed=123, name="ConvMF (Text)")
]

# --- STEP 5: DEFINE METRICS ---
# What defines "good"? RMSE for rating prediction, Recall for ranking.
metrics = [
    cornac.metrics.RMSE(), 
    cornac.metrics.Recall(k=5) # "Out of top 5 recs, how many did the user actually like?"
]

# --- STEP 6: RUN EXPERIMENT ---
experiment = cornac.Experiment(
    eval_method=rs,
    models=models,
    metrics=metrics,
    user_based=True # True for user-based evaluation
)

experiment.run()