import json
from groq import Groq
from fastapi import HTTPException
from fastapi.concurrency import run_in_threadpool
from app.config import settings
from app.schemas import GroqExtraction

client = Groq(api_key=settings.GROQ_API_KEY)

SYSTEM_PROMPT = """
You are an expert text analysis API for Vietnam travel. 
... (Giữ nguyên prompt của bạn ở đây) ...
"""

def _call_groq(user_text: str):
    if not settings.GROQ_API_KEY:
        raise Exception("GROQ_API_KEY is missing")
        
    completion = client.chat.completions.create(
        model=settings.GROQ_MODEL,
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
        return GroqExtraction(**data)
    except Exception as e:
        print(f"Error calling Groq: {e}") # Nên dùng logging thay vì print
        raise HTTPException(status_code=502, detail="AI Service unavailable")