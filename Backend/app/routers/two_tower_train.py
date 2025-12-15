# CELL 2: IMPORT & PREPARE DATA
import pandas as pd
import numpy as np
import tensorflow as tf
from tensorflow.keras import layers, Model, Input, optimizers, callbacks
from transformers import AutoTokenizer, TFAutoModel
from sklearn.model_selection import train_test_split
import ast
import tensorflow as tf
from tensorflow.keras import mixed_precision

# 1. Cấu hình GPU để tránh lỗi "Initialization failed"
gpus = tf.config.experimental.list_physical_devices('GPU')
if gpus:
    try:
        for gpu in gpus:
            # Chỉ cấp phát bộ nhớ khi cần thiết thay vì chiếm hết ngay lập tức
            tf.config.experimental.set_memory_growth(gpu, True)
    except RuntimeError as e:
        print(e)

# 2. Bật Mixed Precision
# Kỹ thuật này dùng float16 cho tính toán giúp giảm VRAM và tăng tốc độ train
# nhưng vẫn giữ float32 cho các biến quan trọng để đảm bảo độ chính xác.
policy = mixed_precision.Policy('mixed_float16')
mixed_precision.set_global_policy(policy)

print("Compute dtype:", policy.compute_dtype)
print("Variable dtype:", policy.variable_dtype)
print("TensorFlow Version:", tf.__version__) # Kiểm tra xem đã về 2.15 chưa

# --- LOAD DATA ---
places_df = pd.read_csv('/kaggle/input/place-with-tags-full/vietnam_tourism_data_200tags_with_province.csv')
ratings_df = pd.read_csv('/kaggle/input/balanced-rating/ratings_clean.csv')

# --- PREPROCESSING (Giữ nguyên logic cũ) ---
places_df['text_desc'] = places_df['ai_input_text'].fillna(places_df['name']).astype(str)

def extract_province(tag_str):
    try: return ast.literal_eval(tag_str)[0] if ast.literal_eval(tag_str) else "Unknown"
    except: return "Unknown"

places_df['province'] = places_df['tags'].apply(extract_province)
province_list = places_df['province'].unique().tolist()
province2idx = {p: i for i, p in enumerate(province_list)}
places_df['province_idx'] = places_df['province'].map(province2idx)

def process_user_prefs(pref_str):
    try: return "I am interested in " + " ".join(ast.literal_eval(pref_str))
    except: return "I am a traveler"

ratings_df['user_text'] = ratings_df['user_prefs'].apply(process_user_prefs)

train_data = ratings_df.merge(places_df[['id', 'text_desc', 'province_idx']], 
                              left_on='place_id', right_on='id', how='left').dropna()

# --- TOKENIZATION ---
MODEL_NAME = 'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2'
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
MAX_LEN = 128

def bert_encode(texts, max_len=MAX_LEN):
    input_ids = []
    attention_masks = []
    for text in texts:
        token = tokenizer(text, max_length=max_len, truncation=True, padding='max_length', add_special_tokens=True)
        input_ids.append(token['input_ids'])
        attention_masks.append(token['attention_mask'])
    return np.array(input_ids), np.array(attention_masks)

print("Tokenizing data...")
user_ids, user_masks = bert_encode(train_data['user_text'].values)
item_ids, item_masks = bert_encode(train_data['text_desc'].values)
province_inputs = train_data['province_idx'].values
targets = train_data['rating'].values / 5.0

X_train_user_id, X_val_user_id, X_train_user_mask, X_val_user_mask, \
X_train_item_id, X_val_item_id, X_train_item_mask, X_val_item_mask, \
X_train_prov, X_val_prov, y_train, y_val = train_test_split(
    user_ids, user_masks, item_ids, item_masks, province_inputs, targets, 
    test_size=0.1, random_state=42
)
print("Data Ready!")
# CELL 3: DEFINE MODEL (OPTIMIZED)
class BertEncoderLayer(layers.Layer):
    def __init__(self, model_name, **kwargs):
        super().__init__(**kwargs)
        self.bert = TFAutoModel.from_pretrained(model_name)
        self.bert.trainable = False 
        
    def call(self, inputs):
        input_ids, attention_mask = inputs
        outputs = self.bert(input_ids=input_ids, attention_mask=attention_mask)
        embeddings = outputs[0] 
        
        # Mean Pooling
        mask_expanded = tf.cast(tf.expand_dims(attention_mask, -1), tf.float32)
        sum_embeddings = tf.reduce_sum(embeddings * mask_expanded, 1)
        sum_mask = tf.clip_by_value(tf.reduce_sum(mask_expanded, 1), 1e-9, 1e9)
        return sum_embeddings / sum_mask

def build_two_tower_model():
    shared_bert_encoder = BertEncoderLayer(MODEL_NAME, name="shared_bert_encoder")

    # --- USER TOWER ---
    u_input_ids = Input(shape=(MAX_LEN,), dtype=tf.int32, name='user_input_ids')
    u_attention_mask = Input(shape=(MAX_LEN,), dtype=tf.int32, name='user_attention_mask')
    
    u_vec = shared_bert_encoder([u_input_ids, u_attention_mask])
    u_vec = layers.Dense(256, activation='relu')(u_vec)
    u_vec = layers.Dropout(0.3)(u_vec)
    u_vec = layers.Dense(128, activation=None)(u_vec)
    u_vec = layers.Lambda(lambda x: tf.math.l2_normalize(x, axis=1), name='user_final_norm')(u_vec)

    # --- ITEM TOWER ---
    i_input_ids = Input(shape=(MAX_LEN,), dtype=tf.int32, name='item_input_ids')
    i_attention_mask = Input(shape=(MAX_LEN,), dtype=tf.int32, name='item_attention_mask')
    i_province = Input(shape=(1,), dtype=tf.int32, name='item_province')
    
    i_text_vec = shared_bert_encoder([i_input_ids, i_attention_mask])
    
    prov_embed = layers.Embedding(len(province_list)+1, 32)(i_province)
    prov_embed = layers.Flatten()(prov_embed)
    
    i_vec = layers.Concatenate()([i_text_vec, prov_embed])
    i_vec = layers.Dense(256, activation='relu')(i_vec)
    i_vec = layers.Dropout(0.3)(i_vec)
    i_vec = layers.Dense(128, activation=None)(i_vec)
    i_vec = layers.Lambda(lambda x: tf.math.l2_normalize(x, axis=1), name='item_final_norm')(i_vec)

    # --- DOT PRODUCT ---
    dot_product = layers.Dot(axes=1)([u_vec, i_vec]) 
    
    # Scale output về 0-1
    output = layers.Lambda(lambda x: (x + 1.0) / 2.0)(dot_product)
    
    # QUAN TRỌNG CHO MIXED PRECISION:
    # Output cuối cùng phải là float32 để đảm bảo loss function tính toán đúng
    output = layers.Activation('linear', dtype='float32', name='output_float32')(output)

    return Model(inputs=[u_input_ids, u_attention_mask, i_input_ids, i_attention_mask, i_province], outputs=output)

# Xây dựng và Compile
tf.keras.backend.clear_session() # Xóa session cũ cho chắc ăn
model = build_two_tower_model()

model.compile(optimizer=optimizers.Adam(learning_rate=0.001), loss='mse', metrics=['mae'])
model.summary()

# CELL 4: TRAINING (Đã sửa lỗi tên file checkpoint)

# SỬA LỖI Ở ĐÂY: Đổi đuôi file từ .h5 thành .weights.h5
checkpoint = callbacks.ModelCheckpoint(
    filepath='best_2tower_frozen.weights.h5', 
    save_best_only=True, 
    monitor='val_loss', 
    save_weights_only=True,
    verbose=1 # Thêm verbose để theo dõi khi nào model được lưu
)

early_stop = callbacks.EarlyStopping(patience=5, restore_best_weights=True)

print("Bắt đầu training...")
history = model.fit(
    x=[X_train_user_id, X_train_user_mask, X_train_item_id, X_train_item_mask, X_train_prov],
    y=y_train,
    validation_data=(
        [X_val_user_id, X_val_user_mask, X_val_item_id, X_val_item_mask, X_val_prov],
        y_val
    ),
    epochs=30,
    batch_size=32,
    callbacks=[checkpoint, early_stop]
)

# CELL 5: TESTING (FIXED)
print("Pre-computing item embeddings...")
all_place_ids, all_place_masks = bert_encode(places_df['text_desc'].values)
all_place_provs = places_df['province_idx'].values

# Lấy Item Tower bằng TÊN
item_tower_model = Model(
    inputs=[model.input[2], model.input[3], model.input[4]],
    outputs=model.get_layer('item_final_norm').output
)

print("Predicting items...")
item_embeddings = item_tower_model.predict([all_place_ids, all_place_masks, all_place_provs], batch_size=64, verbose=1)

# Lấy User Tower bằng TÊN
user_tower_model = Model(
    inputs=[model.input[0], model.input[1]],
    outputs=model.get_layer('user_final_norm').output
)

def recommend(query_text):
    print(f"\nQuery: '{query_text}'")
    q_ids, q_masks = bert_encode([query_text])
    query_vec = user_tower_model.predict([q_ids, q_masks], verbose=0)
    
    # Lúc này query_vec chắc chắn là (1, 64) -> Khớp với item_embeddings
    scores = np.dot(item_embeddings, query_vec.T).flatten()
    top_indices = scores.argsort()[-5:][::-1]
    
    for idx in top_indices:
        place = places_df.iloc[idx]
        print(f"- {place['name']} ({place['province']}) - Score: {scores[idx]:.4f}")

# Test
recommend("I want to go to a beach") # Sở thích chung
recommend("Mountain")             # Tên địa điểm cụ thể (Nó sẽ ra Bà Nà!)
recommend("hiking")           # Cầu Rồng