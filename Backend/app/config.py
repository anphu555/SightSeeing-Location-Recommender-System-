import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")


    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    if not GEMINI_API_KEY:
        raise ValueError("No GEMINI_API_KEY found in environment variables")


    PROJECT_NAME = "Smart Tourism API"
    VERSION = "1.0.0"

    CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
    
    # Lấy thư mục cha của app/ (tức là thư mục Backend/)
    BACKEND_DIR = os.path.dirname(CURRENT_DIR)
    
    # Nối với tên file database
    DATABASE_PATH = os.path.join(BACKEND_DIR, "vietnamtravel.db")

    
    # --- Cấu hình bảo mật ---
    # Trong thực tế, hãy đổi chuỗi này thành một chuỗi ngẫu nhiên dài và bảo mật
    SECRET_KEY = os.getenv("SECRET_KEY", "super_secret_key_sigma_alpha_123")
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 30
settings = Settings()