from fastapi import HTTPException
import google.generativeai as genai

from app.config import settings

from app.main import app
from app.schemas import ChatbotRequest

# Load API Key from .env file
genai.configure(api_key=settings.GEMINI_API_KEY)

# Cái này để giới hạn nội dung chatbot

# 1. Define the System Instruction
system_instruction = """
You are a specialized Tourism and Travel Assistant. 
Your goal is to help users plan trips, recommend destinations, explain local cultures, and provide travel tips in Vietnam.

IMPORTANT RULES:
1. You must ONLY answer questions related to tourism, travel, geography, hotels, food, and sightseeing.
2. If a user asks about math, coding, politics, or general life advice unrelated to travel, you must politely decline.
3. Example refusal: "I'm sorry, I am a travel assistant and can only help with tourism-related queries."
4. Keep your answers helpful, exciting, and concise.
"""

# 2. Initialize the Model with the instruction
model = genai.GenerativeModel(
    'gemini-1.5-flash',
    system_instruction=system_instruction
)



# Tạo route chat cho chatbot
@app.post("/chat")
async def chat_endpoint(request: ChatbotRequest):
    try:
        # Generate response from Gemini
        response = model.generate_content(request.message)
        return {"reply": response.text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



# Co them RAG 

# import os
# import uvicorn
# from fastapi import FastAPI, HTTPException
# from fastapi.middleware.cors import CORSMiddleware
# from pydantic import BaseModel
# import google.generativeai as genai
# from dotenv import load_dotenv

# load_dotenv()
# GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# genai.configure(api_key=GEMINI_API_KEY)

# # --- 1. THE DATABASE (Simple List) ---
# tour_data = [
#     {
#         "name": "Ha Long Bay Cruise",
#         "price": "1,200,000 VND",
#         "duration": "2 Days 1 Night",
#         "highlights": "Kayaking, Cave visiting, Squid fishing"
#     },
#     {
#         "name": "Sapa Trekking Tour",
#         "price": "900,000 VND",
#         "duration": "1 Day",
#         "highlights": "Rice terraces, Hmong village culture, Waterfall"
#     },
#     {
#         "name": "Da Nang & Hoi An Combo",
#         "price": "3,500,000 VND",
#         "duration": "3 Days 2 Nights",
#         "highlights": "Ba Na Hills, Ancient Town, My Khe Beach"
#     }
# ]

# # --- 2. SEARCH FUNCTION ---
# def search_tours(query: str):
#     """Finds tours that match keywords in the user's message."""
#     query = query.lower()
#     results = []
#     for tour in tour_data:
#         # Check if tour name matches the user's query
#         if tour["name"].lower() in query or query in tour["name"].lower(): 
#             results.append(tour)
    
#     # Also return all data if user asks generally for "prices" or "tours"
#     if "price" in query or "list" in query or "tour" in query:
#         return results if results else tour_data[:2] # Return first 2 as examples if no specific match
        
#     return results

# # --- 3. SYSTEM INSTRUCTION ---
# system_instruction = """
# You are a Tourism Sales Assistant. 
# You have access to a specific database of tour packages.
# When a user asks about a tour, use the provided 'Context' to answer.
# If the context is empty, give general travel advice but mention you don't have specific pricing for that yet.
# Do not make up prices. Only use the prices in the Context.
# """

# model = genai.GenerativeModel('gemini-1.5-flash', system_instruction=system_instruction)

# app = FastAPI()

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# class ChatRequest(BaseModel):
#     message: str

# @app.post("/chat")
# async def chat_endpoint(request: ChatRequest):
#     try:
#         # Step A: Search our internal database first
#         relevant_tours = search_tours(request.message)
        
#         # Step B: Create a context string
#         context_str = ""
#         if relevant_tours:
#             context_str = "Here is the internal data found: \n"
#             for tour in relevant_tours:
#                 context_str += f"- Tour: {tour['name']}, Price: {tour['price']}, Duration: {tour['duration']}, Highlights: {tour['highlights']}\n"
#         else:
#             context_str = "No specific internal tour data found for this request."

#         # Step C: Combine Context + User Question
#         full_prompt = f"""
#         Context: {context_str}
        
#         User Question: {request.message}
        
#         Answer:
#         """

#         # Step D: Ask Gemini
#         response = model.generate_content(full_prompt)
#         return {"reply": response.text}

#     except Exception as e:
#         # Print error to terminal for debugging
#         print(f"Error: {e}") 
#         raise HTTPException(status_code=500, detail=str(e))

# if __name__ == "__main__":
#     uvicorn.run(app, host="127.0.0.1", port=8000)