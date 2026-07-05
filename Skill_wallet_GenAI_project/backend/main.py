import uuid
from typing import List, Optional
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from backend import event_analyzer
from backend import topic_generator
from backend import fact_checker
from backend import history_logger
from backend import feedback_logger

app = FastAPI(
    title="Personalized Networking Assistant API",
    description="Backend API for event theme analysis, personalized starter generation, and Wikipedia fact-checking.",
    version="1.0.0"
)

# Enable CORS for Streamlit frontend or direct browser access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For local development, allow all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Pydantic Schemas ---

class EventAnalysisRequest(BaseModel):
    event_description: str = Field(..., description="Text description of the networking event.")
    mock: bool = Field(False, description="Use fast keyword matcher instead of DistilBERT.")

class EventAnalysisResponse(BaseModel):
    themes: List[str] = Field(..., description="Extracted event categories/themes.")

class GenerateConversationRequest(BaseModel):
    event_description: str = Field(..., description="Text description of the networking event.")
    user_interests: str = Field(..., description="Comma-separated topics of interest to the user.")
    mock: bool = Field(False, description="Use fast mockup generation templates.")

class GenerateConversationResponse(BaseModel):
    generation_id: str = Field(..., description="Unique ID for this generation, used for rating feedback.")
    themes: List[str] = Field(..., description="Extracted event categories/themes.")
    conversation_starters: List[str] = Field(..., description="3 custom conversation starters.")

class FactCheckRequest(BaseModel):
    claim: str = Field(..., description="The factual statement or conversation starter to verify.")
    mock: bool = Field(False, description="Use fast keyword-based similarity matching instead of NLI.")

class FactCheckResponse(BaseModel):
    verdict: str = Field(..., description="Verdict: Supported, Refuted, or Neutral.")
    confidence: float = Field(..., description="Confidence score of the NLI evaluation.")
    details: str = Field(..., description="Detailed explanation of the verdict.")
    wikipedia_title: str = Field(..., description="Title of the retrieved Wikipedia article.")
    wikipedia_summary: str = Field(..., description="Summary text from Wikipedia.")
    wikipedia_url: str = Field(..., description="URL of the Wikipedia article.")

class FeedbackRequest(BaseModel):
    generation_id: str = Field(..., description="The ID of the conversation starters generated.")
    rating: str = Field(..., description="User feedback: 'like' or 'dislike'.")

class FeedbackResponse(BaseModel):
    status: str
    message: str

# --- API Routes ---

@app.get("/")
def read_root():
    return {
        "app": "Personalized Networking Assistant API",
        "status": "healthy",
        "models": {
            "theme_extractor": "DistilBERT zero-shot-classification",
            "prompt_generator": "GPT-2 Small",
            "fact_checker": "Wikipedia API + DistilBERT MNLI NLI"
        }
    }

@app.post("/analyze-event", response_model=EventAnalysisResponse)
def analyze_event(payload: EventAnalysisRequest):
    """Extract categories/themes from event description."""
    try:
        themes = event_analyzer.analyze_event_description(payload.event_description, mock=payload.mock)
        return EventAnalysisResponse(themes=themes)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error analyzing event: {str(e)}"
        )

@app.post("/generate-conversation", response_model=GenerateConversationResponse)
def generate_conversation(payload: GenerateConversationRequest):
    """Generate 3 personalized conversation starters, log the query and output to history."""
    try:
        # 1. Analyze description to get themes first
        themes = event_analyzer.analyze_event_description(payload.event_description, mock=payload.mock)
        
        # 2. Generate topics using themes & user interests
        starters = topic_generator.generate_conversation_starters(
            event_description=payload.event_description,
            user_interests=payload.user_interests,
            themes=themes,
            mock=payload.mock
        )
        
        # 3. Log to history
        generation_id = str(uuid.uuid4())
        history_logger.log_generation(
            generation_id=generation_id,
            event_description=payload.event_description,
            user_interests=payload.user_interests,
            themes=themes,
            starters=starters
        )
        
        return GenerateConversationResponse(
            generation_id=generation_id,
            themes=themes,
            conversation_starters=starters
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating conversation: {str(e)}"
        )

@app.post("/fact-check", response_model=FactCheckResponse)
async def fact_check(payload: FactCheckRequest):
    """Verify a claim using Wikipedia and NLI classifier."""
    try:
        # 1. Search Wikipedia
        title, summary, url = await fact_checker.search_wikipedia(payload.claim)
        print("TITLE =", title)
        print("SUMMARY =", summary)
        print("URL =", url)
        if not title:
            return FactCheckResponse(
                verdict="Neutral",
                confidence=0.5,
                details="No relevant Wikipedia article could be found for this claim.",
                wikipedia_title="None Found",
                wikipedia_summary="No Wikipedia data retrieved.",
                wikipedia_url=""
            )
            
        # 2. Verify claim against summary
        result = fact_checker.verify_claim(payload.claim, summary, mock=payload.mock)
        
        return FactCheckResponse(
            verdict=result["verdict"],
            confidence=result["confidence"],
            details=result["details"],
            wikipedia_title=title,
            wikipedia_summary=summary,
            wikipedia_url=url
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error during fact check: {str(e)}"
        )

@app.post("/feedback", response_model=FeedbackResponse)
def submit_feedback(payload: FeedbackRequest):
    """Submit user feedback (like/dislike) for a generated prompt."""
    if payload.rating not in ("like", "dislike"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Rating must be 'like' or 'dislike'."
        )
    try:
        feedback_logger.log_feedback(payload.generation_id, payload.rating)
        return FeedbackResponse(
            status="success",
            message=f"Feedback '{payload.rating}' logged for generation {payload.generation_id}."
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error logging feedback: {str(e)}"
        )

@app.get("/history")
def get_history():
    """Get all past generations logs."""
    return history_logger.get_history()

@app.get("/feedback/stats")
def get_feedback_stats():
    """Get stats on likes/dislikes."""
    return feedback_logger.get_feedback_stats()

@app.post("/history/clear")
def clear_history():
    """Clear history log file."""
    if history_logger.clear_history():
        return {"status": "success", "message": "History cleared successfully."}
    raise HTTPException(status_code=500, detail="Failed to clear history.")

@app.post("/feedback/clear")
def clear_feedback():
    """Clear feedback log file."""
    if feedback_logger.clear_feedback():
        return {"status": "success", "message": "Feedback logs cleared successfully."}
    raise HTTPException(status_code=500, detail="Failed to clear feedback logs.")
