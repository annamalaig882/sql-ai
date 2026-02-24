import logging
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from chatbot import SQLChatbot
from fastapi.middleware.cors import CORSMiddleware
import os

# Configure login
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="SQL AI Assistant API")

# Allow CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify the frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Chatbot
# We initialize it once at startup
try:
    bot = SQLChatbot()
    logger.info("SQL Chatbot initialized successfully.")
except Exception as e:
    logger.error(f"Failed to initialize SQL Chatbot: {e}")
    bot = None

class ChatRequest(BaseModel):
    message: str
    session_id: str = "default_session"
    mode: str = "sql"  # 'sql' or 'general'

class ChatResponse(BaseModel):
    response: str

@app.get("/health")
async def health_check():
    return {"status": "ok", "bot_initialized": bot is not None}

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    if not bot:
        raise HTTPException(status_code=503, detail="Chatbot not initialized")

    try:
        if request.mode == "general":
            # Note: get_general_response in chatbot.py currently uses a hardcoded prompt/model
            # and does not accept session_id for history (it's stateless in the current impl).
            # If we want history for general chat, we'd need to refactor chatbot.py further.
            # For now, we keep it as is.
            response = bot.get_general_response(request.message)
        else:
            response = bot.get_response(request.message, session_id=request.session_id)
        
        return ChatResponse(response=response)
    except Exception as e:
        logger.error(f"Error processing chat request: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/history/clear")
async def clear_history(request: Request):
    # This is a placeholder. Redis clearing logic isn't exposed in SQLChatbot yet.
    # We would need to implement a method in SQLChatbot to clear history for a session.
    # For now, we'll just acknowledge.
    return {"status": "not_implemented_yet", "message": "History clearing via API not yet supported in chatbot.py"}
