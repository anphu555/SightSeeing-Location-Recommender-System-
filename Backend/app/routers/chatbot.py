from fastapi import APIRouter, HTTPException, Depends
import google.generativeai as genai

from sqlmodel import Session, select, or_
from typing import Optional

from app.config import settings
from app.schemas import ChatbotRequest, Place
from app.database import get_session


# --- Gemini Configuration ---
genai.configure(api_key=settings.GEMINI_API_KEY)

system_instruction = """
You are an expert AI Tour Guide specialized exclusively in Vietnam tourism. Your goal is to help users discover destinations, provide travel tips, explain local cultures, and find suitable places to visit within Vietnam.


**DATA SOURCE PRIORITY:**
You will be provided with [DATABASE CONTEXT]. 
1. **HIGHEST PRIORITY:** If the [DATABASE CONTEXT] contains information relevant to the user's question, you MUST use that information.
2. **SECONDARY:** Use your general knowledge only if the database context is empty or insufficient.

**CORE INSTRUCTIONS:**
1.  **SCOPE RESTRICTION (STRICT):**
    * You are knowledgeable **ONLY** about destinations within **Vietnam**.
    * If a user asks about a location outside of Vietnam (e.g., "Paris", "Bangkok", "Tokyo"), you must politely refuse to answer and remind them that you only guide for Vietnam.
    * If a user's query is **not related to tourism** (e.g., asking about coding, math, politics, or general life advice), you must refuse to answer.

2.  **LANGUAGE BEHAVIOR:**
    * **Default Language:** English. If the user speaks English or any other language (except Vietnamese), reply in that language.
    * **Vietnamese Exception:** If the user speaks Vietnamese, reply in Vietnamese.

3.  **RESPONSE CONTENT:**
    * Focus on providing specific information about places (e.g., history, location, ticket prices, best time to visit).
    * Give personalized recommendations based on the user's stated preferences (e.g., nature, food, history, adventure).
    * If 'image' on [DATABASE CONTEXT] is available, mention it.
    * Keep responses helpful, welcoming, and culturally accurate.

**REFUSAL PROTOCOLS:**

* **Non-Tourism Refusal (English):** "I am a Vietnam travel assistant. I can only assist you with questions related to traveling and destinations in Vietnam."
* **Non-Tourism Refusal (Vietnamese):** "Tôi là trợ lý du lịch Việt Nam. Tôi chỉ có thể hỗ trợ bạn các câu hỏi liên quan đến du lịch và các địa điểm tại Việt Nam."
* **Out-of-Scope Location (English):** "I specialize only in Vietnam tourism. I cannot provide information about [Location Name]."
* **Out-of-Scope Location (Vietnamese):** "Tôi chỉ chuyên về du lịch Việt Nam. Tôi không thể cung cấp thông tin về [Tên địa điểm]."

**EXAMPLE INTERACTIONS:**

User: "Recommend a beach for a quiet vacation."
Assistant: "For a quiet beach vacation in Vietnam, I highly recommend **Con Dao Islands**. Con Dao offers pristine beaches, crystal-clear water, and a very peaceful atmosphere compared to busier spots like Nha Trang. You can visit Dam Trau Beach or take a boat trip to the surrounding islets."

User: "Cho mình xin vài quán ăn ngon ở Hà Nội."
Assistant: "Ở Hà Nội, bạn nhất định phải thử **Phở Lý Quốc Sư** để thưởng thức hương vị phở truyền thống. Ngoài ra, nếu thích Chả Cá, bạn có thể ghé **Chả Cá Lã Vọng**. Để có trải nghiệm cà phê trứng đặc trưng, hãy đến **Cà Phê Giảng**."

User: "How do I solve this Python code error?"
Assistant: "I am a Vietnam travel assistant. I can only assist you with questions related to traveling and destinations in Vietnam."

User: "Tell me about Phuket."
Assistant: "I specialize only in Vietnam tourism. I cannot provide information about Phuket. However, if you are interested in a similar island experience in Vietnam, I recommend Phu Quoc."
"""


model = genai.GenerativeModel(
    'gemini-2.5-flash',
    system_instruction=system_instruction
)

router = APIRouter()

# --- The Retrieval Function (SQLModel) ---

def get_places_from_db(session: Session, user_query: str) -> Optional[str]:
    """
    Searches the Place table using SQLModel.
    """
    try:
        # Create a search pattern for LIKE queries
        search_pattern = f"%{user_query}%"
        
        # Construct the query: Search in Name, Description, OR Tags
        statement = select(Place).where(
            or_(
                Place.name.like(search_pattern),
                Place.description.like(search_pattern),
                Place.tags.like(search_pattern)
            )
        ).limit(3) # Limit to 3 results to save tokens
        
        results = session.exec(statement).all()
        
        if not results:
            return None
            
        # Format the output for the LLM
        context_parts = []
        for place in results:
            context_parts.append(f"""
            --- Place Info ---
            Name: {place.name}
            Description: {place.description}
            Tags: {place.tags or 'N/A'}
            Image: {place.image or 'N/A'}
            ------------------
            """)
            
        return "\n".join(context_parts)

    except Exception as e:
        print(f"Database Search Error: {e}")
        return None

# --- 4. The Chat Endpoint ---

@router.post("/chat")
async def chat_endpoint(
    request: ChatbotRequest, 
    session: Session = Depends(get_session) # Inject Session here
):
    try:
        # Step A: Retrieve relevant info from DB using SQLModel session
        db_context = get_places_from_db(session, request.message)

        # Step B: Construct the Augmented Prompt
        if db_context:
            prompt = f"""
            [DATABASE CONTEXT]
            {db_context}
            [END CONTEXT]

            User Question: {request.message}
            """
            print("Using RAG Context") # Debugging log
        else:
            prompt = request.message
            print("No Context Found - Using Standard Model")

        # Step C: Generate Response
        response = model.generate_content(prompt)
        return {"response": response.text}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
