import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
    PROJECT_NAME = "Smart Tourism API"
    VERSION = "1.0.0"

    CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
    
    # Lấy thư mục cha của app/ (tức là thư mục Backend/)
    BACKEND_DIR = os.path.dirname(CURRENT_DIR)
    
    # Nối với tên file database
    DATABASE_PATH = os.path.join(BACKEND_DIR, "travel_final.db")

    
    # DATABASE_PATH = "travel_final.db"
settings = Settings()