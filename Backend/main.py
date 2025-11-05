from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import os, json
from groq import Groq
from data import PLACES
from dotenv import load_dotenv
load_dotenv()  # take environment variables from .env if present
app = FastAPI(
    title="Smart Tourism API",
    version="1.0.0",
    docs_url="/api/v1/docs",     # Swagger UI
    redoc_url="/api/v1/redoc"    # alternative docs
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # tighten later
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- config ----------
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    print("WARNING: GROQ_API_KEY not set. /recommend will fail until you export it.")
client = Groq(api_key=GROQ_API_KEY)

GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")

SYSTEM_PROMPT = """
You are an expert text analysis API for Vietnam travel. Your job is to
read a user's text and extract specific details. You must respond in
ONLY a valid JSON format.

The JSON object you return must have these five keys:

1. "location": A list of all specific provinces in Vietnam mentioned
   (e.g., "Quang Ninh", "Da Nang", "Lam Dong", "Kien Giang").
   If no specific province is mentioned, return an empty list [].

2. "type": Categorize the type of place. Must be one of:
   "beach", "forest", "mountain", "island", "city", "unknown".

3. "budget": Categorize the budget. Must be one of:
   "cheap", "moderate", "expensive", "unknown".

4. "weather": Categorize the weather. Must be one of:
   "warm", "hot", "cool", "cold", "unknown".

5. "crowded": Categorize the crowdedness. Must be one of:
   "crowded", "average", "empty", "unknown".

Do not write any text outside of the JSON object.
""".strip()

# ---------- schemas ----------
class RecommendRequest(BaseModel):
    user_text: str = Field(..., example="i like mountains in Viet Nam and cool weather")
    top_k: int = Field(5, ge=1, le=20)

class GroqExtraction(BaseModel):
    location: List[str]
    type: str
    budget: str
    weather: str
    crowded: str

class PlaceOut(BaseModel):
    name: str
    country: str
    province: str
    region: str
    themes: List[str]
    score: float

class RecommendResponse(BaseModel):
    extraction: GroqExtraction
    results: List[PlaceOut]

# ---------- LLM call ----------
def _call_groq(user_text: str) -> Dict[str, Any]:
    """Sync call (Groq client is sync). Run this in a threadpool from async context."""
    completion = client.chat.completions.create(
        model=GROQ_MODEL,
        temperature=0.0,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_text},
        ],
    )
    content = completion.choices[0].message.content
    return json.loads(content)

async def extract_with_groq(user_text: str) -> GroqExtraction:
    try:
        data = await run_in_threadpool(_call_groq, user_text)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Groq error: {e}")
    # basic shape validation
    try:
        return GroqExtraction(**data)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Bad LLM JSON: {data} ({e})")

# ---------- scoring ----------
TYPE_TO_THEME = {
    "mountain": ["mountain"],
    "beach": ["beach"],
    "island": ["island", "snorkeling"],
    "forest": ["nature", "forest"],
    "city": ["city", "culture"],
    "unknown": []
}

def score_place(ex: GroqExtraction, place: Dict[str, Any]) -> float:
    # province match: strong boost if user mentioned same province
    prov_boost = 0.0
    if ex.location:
        # compare ignoring accents and case (simple norm)
        def norm(s): return s.lower().replace(" ", "")
        user_provs = {norm(p) for p in ex.location}
        if norm(place.get("province", "")) in user_provs:
            prov_boost = 0.6

    # type -> themes overlap (main semantic driver)
    target_themes = TYPE_TO_THEME.get(ex.type, [])
    theme_overlap = len(set(t.lower() for t in place["themes"]) & set(t.lower() for t in target_themes))
    theme_score = theme_overlap / max(len(place["themes"]), 1)

    # small heuristics from weather/crowded/budget you can expand later
    # for now: cool -> tiny boost to Đà Lạt-style places already captured by theme
    weather_bonus = 0.1 if (ex.weather in {"cool", "cold"} and "cool weather" in [t.lower() for t in place["themes"]]) else 0.0

    return round(prov_boost + theme_score + weather_bonus, 4)

def rank_places(ex: GroqExtraction, top_k: int) -> List[PlaceOut]:
    scored = []
    for p in PLACES:
        s = score_place(ex, p)
        scored.append(PlaceOut(
            name=p["name"],
            country=p["country"],
            province=p["province"],
            region=p["region"],
            themes=p["themes"],
            score=s
        ))
    scored.sort(key=lambda x: x.score, reverse=True)
    return scored[:top_k]

# ---------- endpoints ----------
@app.get("/health")
def health():
    return {"status": "ok"}
@app.get("/")
def root():
    return {"message": "Welcome to Smart Tourism API! Visit /api/v1/docs for API docs."}

@app.post("/api/v1/recommend", response_model=RecommendResponse)
async def recommend(req: RecommendRequest):
    if not GROQ_API_KEY:
        raise HTTPException(status_code=500, detail="Server missing GROQ_API_KEY")
    extraction = await extract_with_groq(req.user_text)
    results = rank_places(extraction, req.top_k)
    return RecommendResponse(extraction=extraction, results=results)
