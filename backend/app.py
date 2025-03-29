from typing import List, Optional, Dict, Any
from fastapi import FastAPI, HTTPException, Security, Depends, Body
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.middleware.cors import CORSMiddleware
from supabase import create_client, Client
from pydantic import BaseModel
from dotenv import load_dotenv
from openai import AsyncOpenAI
from pathlib import Path
import httpx
import sys
import os
import logging
# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

from pydantic_ai.messages import (
    ModelRequest,
    ModelResponse,
    UserPromptPart,
    TextPart
)

from parts_select_ai_expert import parts_select_expert, PartsSelectAIDeps

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI()
security = HTTPBearer()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Supabase setup
supabase: Client = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SERVICE_KEY")
)

# OpenAI setup
# openai_client = AsyncOpenAI(api_key=os.getenv("DEEPSEEK_API_KEY"), base_url=os.getenv("DEEPSEEK_API_URL"))
openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Request/Response Models
class AgentRequest(BaseModel):
    query: str
    user_id: str
    request_id: str
    session_id: str

class AgentResponse(BaseModel):
    success: bool
    ai_content: Optional[str] = None

def verify_token(credentials: HTTPAuthorizationCredentials = Security(security)) -> bool:
    """Verify the bearer token against environment variable."""
    expected_token = os.getenv("API_BEARER_TOKEN")
    if not expected_token:
        raise HTTPException(
            status_code=500,
            detail="API_BEARER_TOKEN environment variable not set"
        )
    if credentials.credentials != expected_token:
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication token"
        )
    return True    

async def fetch_conversation_history(session_id: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Fetch the most recent conversation history for a session."""
    try:
        response = supabase.table("messages") \
            .select("*") \
            .eq("session_id", session_id) \
            .order("timestamp") \
            .limit(limit) \
            .execute()
        
        # Convert to list and reverse to get chronological order
        messages = response.data
        return messages
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch conversation history: {str(e)}")


# Also add more detailed logging to the store_message function
async def store_message(session_id: str, message_type: str, content: str, data: Optional[Dict] = None):
    """Store a message in the Supabase messages table."""
    message_obj = {
        "type": message_type,
        "content": content
    }
    if data:
        message_obj["data"] = data

    try:
        logger.info(f"Attempting to store message in Supabase: {message_type} for session {session_id}")
        result = supabase.table("messages").insert({
            "session_id": session_id,
            "message": message_obj
        }).execute()
        logger.info(f"Message stored successfully: {result}")
        return result
    except Exception as e:
        logger.error(f"Failed to store message in Supabase: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to store message: {str(e)}")

@app.post("/api/parts-select-ai-expert", response_model=AgentResponse)
async def parts_select_ai_expert_endpoint(
    request: AgentRequest,
    authenticated: bool = Depends(verify_token)
):
    try:
        logger.info(f"Received request: {request}")
        
        # Store user's query
        logger.info(f"Storing user query: {request.query}")
        try:
            await store_message(
                session_id=request.session_id,
                message_type="human",
                content=request.query
            )
            logger.info("Successfully stored user query")
        except Exception as e:
            logger.error(f"Error storing user query: {str(e)}")
            raise
        
        # Fetch conversation history
        conversation_history = await fetch_conversation_history(request.session_id)
        logger.info(f"Fetched conversation history: {len(conversation_history)} messages")
        
        # Convert conversation history to format expected by agent
        messages = []
        for msg in conversation_history:
            msg_data = msg["message"]
            msg_type = msg_data["type"]
            msg_content = msg_data["content"]
            msg = ModelRequest(parts=[UserPromptPart(content=msg_content)]) if msg_type == "human" else ModelResponse(parts=[TextPart(content=msg_content)])
            messages.append(msg)

        # Initialize agent dependencies
        async with httpx.AsyncClient() as client:
            deps = PartsSelectAIDeps(
                supabase=supabase,
                openai_client=openai_client
            )

            # Run the agent with conversation history
            logger.info("Running agent with conversation history")
            result = await parts_select_expert.run(
                request.query,
                message_history=messages,
                deps=deps
            )
            logger.info("Agent execution completed successfully")

        # Store agent's response
        logger.info("Storing agent response")
        ai_content = result.data
        try:
            await store_message(
                session_id=request.session_id,
                message_type="ai",
                content=ai_content,
                data={"request_id": request.request_id}
            )
            logger.info("Successfully stored agent response")
        except Exception as e:
            logger.error(f"Error storing agent response: {str(e)}")
            raise

        # Return success along with the AI content
        return {"success": True, "ai_content": ai_content}

    except Exception as e:
        logger.error(f"Error processing agent request: {str(e)}", exc_info=True)
        # Store error message in conversation
        try:
            await store_message(
                session_id=request.session_id,
                message_type="ai",
                content="I apologize, but I encountered an error processing your request.",
                data={"error": str(e), "request_id": request.request_id}
            )
        except Exception as store_error:
            logger.error(f"Error storing error message: {str(store_error)}")
        
        return AgentResponse(success=False)
    
@app.get("/api/messages")
async def get_messages(
    session_id: str,
    authenticated: bool = Depends(verify_token)
):
    """Fetch messages for a specific session."""
    try:
        # Fetch messages for the session
        response = supabase.table("messages") \
            .select("*") \
            .eq("session_id", session_id) \
            .order("timestamp") \
            .execute()
        
        return response.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch messages: {str(e)}")

# And add a simple test endpoint to directly test Supabase connection
@app.get("/api/test-supabase")
async def test_supabase_connection(authenticated: bool = Depends(verify_token)):
    """Test endpoint to verify Supabase connection."""
    try:
        # Try to query the messages table
        response = supabase.table("messages").select("count", count="exact").execute()
        count = response.count if hasattr(response, 'count') else 'unknown'
        return {"success": True, "message": f"Successfully connected to Supabase. Messages count: {count}"}
    except Exception as e:
        logger.error(f"Supabase connection test failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Supabase connection test failed: {str(e)}")


class WelcomeMessageRequest(BaseModel):
    session_id: str
    user_id: str
    request_id: str

@app.post("/api/save-welcome-message", response_model=AgentResponse)
async def save_welcome_message_endpoint(
    request: WelcomeMessageRequest,
    authenticated: bool = Depends(verify_token)
):
    """Endpoint to save a welcome message for new sessions."""
    try:
        session_id = request.session_id
        request_id = request.request_id
        
        welcome_message = "Hi, how can I help you today?"
        
        # Store the welcome message
        await store_message(
            session_id=session_id,
            message_type="ai",
            content=welcome_message,
            data={"request_id": request_id, "is_welcome": True}
        )
        
        logger.info(f"Saved welcome message for session {session_id}")
        return { "success":True, "ai_content":"Success at save welcome message" }
        
    except Exception as e:
        logger.error(f"Error saving welcome message: {str(e)}", exc_info=True)
        return { "success":False, "ai_content":"Failed to save welcome message" }
    
@app.get("/api/messages/latest")
async def get_latest_message(
    session_id: str,
    authenticated: bool = Depends(verify_token)
):
    """Fetch the most recent message for a session."""
    try:
        # Fetch the most recent message
        response = supabase.table("messages") \
            .select("*") \
            .eq("session_id", session_id) \
            .order("timestamp") \
            .limit(1) \
            .execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="No messages found for this session")
        
        return response.data[0]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch latest message: {str(e)}")
    
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
