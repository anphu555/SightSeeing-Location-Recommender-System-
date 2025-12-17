import json
from groq import Groq
from fastapi import HTTPException
from fastapi.concurrency import run_in_threadpool
from app.config import settings
# from backend.app.old.schemas import GroqExtraction
from app.schemas import GroqExtraction

client = Groq(api_key=settings.GROQ_API_KEY)

SYSTEM_PROMPT = """
You are an expert text analysis API for Vietnam travel. Your job is to
read a user's text and extract specific details. You must respond in
ONLY a valid JSON format.

The JSON object you return must have these six keys:

1. "location": A list of provinces the user WANTS to go to.
2. "exclude_locations": A list of provinces the user wants to AVOID
   or wants recommendations "similar to" (e.g., "like Vung Tau").
3. "type": Categorize the type of place. Must be one of:
   "beach", "forest", "mountain", "island", "city", "unknown".
4. "budget": Categorize the budget. Must be one of:
   "cheap", "moderate", "expensive", "unknown".
5. "weather": Categorize the weather. Must be one of:
   "warm", "hot", "cool", "cold", "unknown".
6. "crowded": Categorize the crowdedness. Must be one of:
   "crowded", "average", "empty", "unknown".

--- EXAMPLES ---

USER TEXT: "i like mountains in Viet Nam and cool weather"
YOUR JSON:
{
  "location": [],
  "exclude_locations": [],
  "type": "mountain",
  "budget": "unknown",
  "weather": "cool",
  "crowded": "unknown"
}

USER TEXT: "show me islands in Quang Ninh"
YOUR JSON:
{
  "location": ["Quang Ninh"],
  "exclude_locations": [],
  "type": "island",
  "budget": "unknown",
  "weather": "unknown",
  "crowded": "unknown"
}

USER TEXT: "Hmmm, i would love to go somewhere with great oceanic view that is similar to Vung Tau"
YOUR JSON:
{
  "location": [],
  "exclude_locations": ["Ba Ria - Vung Tau"],
  "type": "beach",
  "budget": "unknown",
  "weather": "unknown",
  "crowded": "unknown"
}
"""

def _call_groq(user_text: str):
    if not settings.GROQ_API_KEY:
        raise Exception("GROQ_API_KEY is missing")
        
    completion = client.chat.completions.create(
        model=settings.GROQ_MODEL,
        temperature=0.0,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT}, # Prompt này đã có chữ JSON
            {"role": "user", "content": user_text},
        ],
    )
    content = completion.choices[0].message.content
    return json.loads(content)

async def extract_with_groq(user_text: str) -> GroqExtraction:
    try:
        data = await run_in_threadpool(_call_groq, user_text)

        userPrompt = GroqExtraction(**data)

        if isVaguePrompt(userPrompt) == True:
            # request to prompt again!!!
            # return 
            ...

        return userPrompt
    
    except Exception as e:
        print(f"Error calling Groq: {e}") 
        raise HTTPException(status_code=502, detail="AI Service unavailable")
    
def isVaguePrompt(data: GroqExtraction) -> bool:
    unknownCount = 0
    if data.type == "unknown":
        unknownCount += 1
    # if data.budget == "unknown":
        # unknownCount += 1
    if data.weather == "unknown":
        unknownCount += 1
    if data.crowded == "unknown":
        unknownCount += 1
    
    if unknownCount > 2:
        return True
    return False
      