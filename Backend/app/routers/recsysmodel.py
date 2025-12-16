import os
# Đặt Keras Backend là TensorFlow trước khi import bất cứ gì khác liên quan đến TF/Keras
os.environ["KERAS_BACKEND"] = "tensorflow"

import pickle
import pandas as pd
import numpy as np
import tensorflow as tf
import keras # Import Keras 3
from keras import layers, Model, Input, saving
from transformers import AutoTokenizer, TFAutoModel
from pathlib import Path
from typing import Dict, Any, Tuple

# --- CONFIG & PATHS ---
MODEL_PATH = Path(__file__).parent
MODEL_NAME = 'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2'
MAX_LEN = 128

# Tên file đã lưu từ bước trước
WEIGHTS_FILE = MODEL_PATH / 'best_2tower_frozen.weights.h5'
EMBEDDINGS_FILE = MODEL_PATH / 'item_embeddings.pkl'
METADATA_FILE = MODEL_PATH / 'places_metadata.csv'
PROVINCE_DICT_FILE = MODEL_PATH / 'province_dictionary.pkl'

# --- 1. MODEL ARCHITECTURE (Đảm bảo khớp với lúc train) ---
# Đăng ký lớp để có thể tải trọng số đúng
@saving.register_keras_serializable() 
class BertEncoderLayer(layers.Layer):
    """Custom Layer để đóng gói TFAutoModel và thực hiện Mean Pooling."""
    def __init__(self, model_name, **kwargs):
        super().__init__(**kwargs)
        self.model_name = model_name
        # Tải mô hình BERT
        self.bert = TFAutoModel.from_pretrained(model_name, from_pt=True) # from_pt=True nếu dùng PT weights
        self.bert.trainable = False 
        
    def call(self, inputs):
        input_ids, attention_mask = inputs
        outputs = self.bert(input_ids=input_ids, attention_mask=attention_mask)
        embeddings = outputs.last_hidden_state
        
        # Mean Pooling
        mask_expanded = tf.cast(tf.expand_dims(attention_mask, -1), tf.float32)
        sum_embeddings = tf.reduce_sum(embeddings * mask_expanded, 1)
        sum_mask = tf.clip_by_value(tf.reduce_sum(mask_expanded, 1), 1e-9, 1e9)
        return sum_embeddings / sum_mask

    def get_config(self):
        config = super().get_config()
        config.update({"model_name": self.model_name})
        return config

def build_two_tower_model(num_provinces):
    """Hàm dựng lại kiến trúc model."""
    shared_bert_encoder = BertEncoderLayer(MODEL_NAME, name="shared_bert_encoder")

    # --- USER TOWER ---
    u_input_ids = Input(shape=(MAX_LEN,), dtype="int32", name='user_input_ids')
    u_attention_mask = Input(shape=(MAX_LEN,), dtype="int32", name='user_attention_mask')
    
    u_vec = shared_bert_encoder([u_input_ids, u_attention_mask])
    u_vec = layers.Dense(256, activation='relu')(u_vec)
    u_vec = layers.Dropout(0.3)(u_vec)
    u_vec = layers.Dense(128, activation=None)(u_vec)
    u_vec = layers.Lambda(lambda x: tf.math.l2_normalize(x, axis=1), name='user_final_norm')(u_vec)
    user_tower = Model(inputs=[u_input_ids, u_attention_mask], outputs=u_vec, name='user_tower')

    # --- ITEM TOWER (Dựng toàn bộ model để tải trọng số đúng cách) ---
    i_input_ids = Input(shape=(MAX_LEN,), dtype="int32", name='item_input_ids')
    i_attention_mask = Input(shape=(MAX_LEN,), dtype="int32", name='item_attention_mask')
    i_province = Input(shape=(1,), dtype="int32", name='item_province')
    
    i_text_vec = shared_bert_encoder([i_input_ids, i_attention_mask])
    
    # Embedding Tỉnh/Thành
    prov_embed = layers.Embedding(num_provinces + 1, 32)(i_province)
    prov_embed = layers.Flatten()(prov_embed)
    
    i_vec = layers.Concatenate()([i_text_vec, prov_embed])
    i_vec = layers.Dense(256, activation='relu')(i_vec)
    i_vec = layers.Dropout(0.3)(i_vec)
    i_vec = layers.Dense(128, activation=None)(i_vec)
    i_vec = layers.Lambda(lambda x: tf.math.l2_normalize(x, axis=1), name='item_final_norm')(i_vec)

    # Full Model
    dot_product = layers.Dot(axes=1)([user_tower.output, i_vec]) 
    output = layers.Lambda(lambda x: (x + 1.0) / 2.0)(dot_product)
    output = layers.Activation('linear', dtype='float32', name='output_float32')(output)

    full_model = Model(
        inputs=[u_input_ids, u_attention_mask, i_input_ids, i_attention_mask, i_province], 
        outputs=output
    )
    return full_model, user_tower

# --- 2. ENCODING UTILITY ---
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)

def bert_encode(texts: list) -> Tuple[tf.Tensor, tf.Tensor]:
    """Tokenize văn bản đầu vào và trả về Tensor."""
    if not texts:
        # Trả về tensor rỗng để tránh lỗi shape, nhưng logic sau đó nên kiểm tra
        return tf.constant([], dtype=tf.int32, shape=(0, MAX_LEN)), tf.constant([], dtype=tf.int32, shape=(0, MAX_LEN))
    
    token = tokenizer(
        texts, 
        max_length=MAX_LEN, 
        truncation=True, 
        padding='max_length', 
        add_special_tokens=True,
        return_tensors='tf' # Trả về TensorFlow tensor
    )
    return token['input_ids'], token['attention_mask']

# --- 3. MODEL LOADER (Singleton Pattern) ---
class RecSysModel:
    """Class Singleton để tải Model và Data chỉ một lần khi server khởi động."""
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(RecSysModel, cls).__new__(cls)
            cls._instance.model_data = cls._instance._load_model_and_data()
        return cls._instance

    def _load_model_and_data(self) -> Dict[str, Any]:
        import logging
        logger = logging.getLogger(__name__)
        logger.info("\n--- Đang tải mô hình Two-Tower và dữ liệu RecSys... ---")
        
        # 1. Load Data
        try:
            # Load metadata và embeddings
            places_df = pd.read_csv(METADATA_FILE)
            with open(PROVINCE_DICT_FILE, 'rb') as f:
                province2idx = pickle.load(f)
            with open(EMBEDDINGS_FILE, 'rb') as f:
                item_embeddings = pickle.load(f)
        except Exception as e:
            logger.error(f"❌ Lỗi tải dữ liệu RecSys: {e}")
            raise Exception(f"Không tìm thấy hoặc không thể tải file RecSys cần thiết: {e}")

        # 2. Build and Load Model
        num_provinces = len(province2idx)
        try:
            # Build full model để khớp kiến trúc lúc train
            full_model, user_tower_model = build_two_tower_model(num_provinces)
            
            if WEIGHTS_FILE.exists():
                full_model.load_weights(str(WEIGHTS_FILE))
                logger.info(f"✅ Đã tải trọng số từ {WEIGHTS_FILE} thành công.")
            else:
                logger.warning(f"⚠️ Cảnh báo: Không tìm thấy file trọng số {WEIGHTS_FILE}. Dùng model khởi tạo.")
                
        except Exception as e:
            logger.error(f"❌ Lỗi tải/load model RecSys: {e}")
            # Lỗi này có thể do phiên bản TF/Keras hoặc thư viện Transformers
            raise Exception(f"Lỗi nghiêm trọng khi khởi tạo/tải trọng số mô hình: {e}")

        logger.info("--- Tải RecSys hoàn tất. ---")
        
        return {
            "item_embeddings": item_embeddings,
            "places_df": places_df,
            "province2idx": province2idx,
            "user_tower_model": user_tower_model, # Chỉ dùng User Tower cho inference
        }

# Global instance
RECSYS_MODEL = None

def initialize_recsys():
    """Initialize the RecSys model on application startup."""
    import logging
    logger = logging.getLogger(__name__)
    global RECSYS_MODEL
    if RECSYS_MODEL is None:
        try:
            logger.info("Initializing RECSYS_MODEL singleton...")
            RECSYS_MODEL = RecSysModel()
            logger.info(f"✅ RECSYS_MODEL initialized successfully: {RECSYS_MODEL}")
        except Exception as e:
            logger.error(f"❌ Failed to initialize RECSYS_MODEL: {e}")
            raise
    else:
        logger.info(f"RECSYS_MODEL already initialized: {RECSYS_MODEL}")
    return RECSYS_MODEL

def get_recsys_model():
    """Get the initialized RecSys model instance."""
    return RECSYS_MODEL