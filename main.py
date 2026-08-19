import sys
import os
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from fastapi import FastAPI, HTTPException, status
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn


from rag_engine import TravelRAGEngine

# Ensure Windows terminal handles UTF-8 clean output
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")


# ---------------------------------------------------------------------------
# 1. Initialize FastAPI Application
# ---------------------------------------------------------------------------
app = FastAPI(
    title="🌍 Travel RAG AI Assistant API",
    description="Production-grade Retrieval-Augmented Generation (RAG) backend powered by LangChain, ChromaDB, HuggingFace embeddings, and Google Gemini.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Enable CORS for web and frontend integrations
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global engine instance (singleton)
engine: Optional[TravelRAGEngine] = None


@app.on_event("startup")
def startup_event():
    """Initializes the RAG Engine and ensures ChromaDB vectors are ready on server startup."""
    global engine
    print("\n[FastAPI Startup] Initializing Travel RAG Engine...")
    engine = TravelRAGEngine()
    engine.build_vector_store(force_reload=False)
    print("[FastAPI Startup] Ready to serve queries!\n")


from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# Mount static files folder
app.mount("/static", StaticFiles(directory="static"), name="static")

# ---------------------------------------------------------------------------
# 2. Pydantic Request & Response Schemas
# ---------------------------------------------------------------------------
class ChatMessage(BaseModel):
    role: str = Field(..., example="user", description="Message author ('user' or 'assistant')")
    content: str = Field(..., example="What are the best beaches?", description="Message content")


class ImageItem(BaseModel):
    title: str
    url: str


class QueryRequest(BaseModel):
    query: str = Field(..., example="What are the best seafood dishes and places in Goa?", description="The travel question to ask.")
    destination: Optional[str] = Field(None, example="Goa", description="Optional destination filter (e.g. Goa, Mumbai, Bangalore, Gujarat, Uttar Pradesh). Leave empty/null for all destinations.")
    top_k: Optional[int] = Field(None, example=4, description="Optional number of context chunks to retrieve.")
    chat_history: Optional[List[ChatMessage]] = Field(default_factory=list, description="Prior conversation messages for multi-turn memory.")
    image_data: Optional[str] = Field(None, description="Optional Base64 encoded image data for visual landmark analysis.")


class SourceItem(BaseModel):
    destination: str
    source: str
    snippet: str
    url: Optional[str] = None


class QueryResponse(BaseModel):
    query: str
    destination_filter: Optional[str]
    answer: str
    sources: List[SourceItem]
    images: List[ImageItem] = Field(default_factory=list)


class ItineraryRequest(BaseModel):
    destination: str = Field(..., example="Goa", description="Destination name for itinerary")
    days: int = Field(3, example=3, description="Number of days")
    budget: Optional[str] = Field("Mid-Range", example="Mid-Range")
    interests: Optional[List[str]] = Field(default_factory=list)
    pace: Optional[str] = Field("Moderate", example="Moderate")


class ItineraryResponse(BaseModel):
    destination: str
    days: int
    itinerary: str
    sources: List[SourceItem]
    images: List[ImageItem] = Field(default_factory=list)


class ReindexResponse(BaseModel):
    status: str
    total_vectors: int
    message: str


# ---------------------------------------------------------------------------
# 3. REST API Endpoints
# ---------------------------------------------------------------------------
@app.get("/", tags=["General"], response_class=FileResponse)
def root():
    """Serves the interactive Web UI with caching disabled for instant updates."""
    return FileResponse(
        "static/index.html",
        headers={"Cache-Control": "no-cache, no-store, must-revalidate", "Pragma": "no-cache", "Expires": "0"}
    )


@app.get("/api/info", tags=["General"])
def api_info():
    """Welcome endpoint with API details and links."""
    return {
        "app": "Travel RAG AI Assistant API",
        "status": "online",
        "interactive_docs": "/docs",
        "available_destinations": ["Goa", "Mumbai", "Bangalore", "Gujarat", "Uttar Pradesh"]
    }


@app.get("/health", tags=["General"])
def health_check():
    """Health check endpoint to verify vector store and engine status."""
    global engine
    if engine is None or engine.vector_store is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="RAG Engine not initialized.")
    
    count = engine.vector_store._collection.count()
    return {
        "status": "healthy",
        "total_vectors_in_db": count,
        "embedding_model": "sentence-transformers/all-MiniLM-L6-v2"
    }


@app.post("/query", response_model=QueryResponse, tags=["RAG Pipeline"])
def query_travel_rag(request: QueryRequest):
    """Executes semantic retrieval from ChromaDB and generates grounded travel advice with conversational memory and vision."""
    global engine
    if engine is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="RAG Engine is starting up.")

    try:
        dest_filter = request.destination.strip() if request.destination and request.destination.strip() else None
        history = [msg.dict() for msg in request.chat_history] if request.chat_history else []
        res = engine.generate_answer(
            query=request.query,
            destination_filter=dest_filter,
            chat_history=history,
            image_data=request.image_data
        )
        
        return QueryResponse(
            query=request.query,
            destination_filter=dest_filter,
            answer=res["answer"],
            sources=res["sources"],
            images=res.get("images", [])
        )

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@app.post("/query/stream", tags=["RAG Pipeline"])
def query_travel_rag_stream(request: QueryRequest):
    """Streams real-time token generation for fast responsive user feedback."""
    global engine
    if engine is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="RAG Engine is starting up.")

    dest_filter = request.destination.strip() if request.destination and request.destination.strip() else None
    history = [msg.dict() for msg in request.chat_history] if request.chat_history else []

    return StreamingResponse(
        engine.generate_answer_stream(
            query=request.query,
            destination_filter=dest_filter,
            chat_history=history,
            image_data=request.image_data
        ),
        media_type="text/event-stream"
    )



@app.post("/itinerary", response_model=ItineraryResponse, tags=["RAG Pipeline"])
def generate_itinerary(request: ItineraryRequest):
    """Generates a structured day-by-day itinerary for a destination using verified RAG knowledge."""
    global engine
    if engine is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="RAG Engine is starting up.")

    try:
        query = f"Create a detailed {request.days}-day travel itinerary for {request.destination} with a {request.budget} budget. Include daily morning, afternoon, and evening plans, local food highlights, transportation, and practical travel tips."
        res = engine.generate_answer(query=query, destination_filter=request.destination)
        
        return ItineraryResponse(
            destination=request.destination,
            days=request.days,
            itinerary=res["answer"],
            sources=res["sources"]
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@app.post("/reindex", response_model=ReindexResponse, tags=["Management"])
@app.post("/ingest", response_model=ReindexResponse, tags=["Management"])
def reindex_knowledge_base():
    """Forces re-indexing of raw text files in data/ into ChromaDB with deduplication."""
    global engine
    if engine is None:
        engine = TravelRAGEngine()

    try:
        result = engine.ingest_documents(force_reload=True)
        return ReindexResponse(
            status=result["status"],
            total_vectors=result["total_vectors"],
            message="Successfully re-indexed documents from data/ into ChromaDB!"
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# ---------------------------------------------------------------------------
# 4. CLI Runner & Main Entry
# ---------------------------------------------------------------------------
def run_cli():
    """Interactive terminal mode."""
    print("=" * 60)
    print("       🌍 AI Travel RAG Assistant - Interactive CLI 🌍")
    print("=" * 60)
    eng = TravelRAGEngine()
    eng.build_vector_store(force_reload=False)
    
    print("\nReady! Enter questions, 'reindex' to rebuild, or 'exit' to quit.\n")
    while True:
        try:
            q = input("\n👉 Enter travel question: ").strip()
            if not q:
                continue
            if q.lower() in ["exit", "quit", "q"]:
                break
            if q.lower() == "reindex":
                res = eng.ingest_documents(force_reload=True)
                print(f"[Success] Reindexed {res['total_vectors']} vectors!")
                continue
            dest = input("📍 Destination filter (or press Enter for all): ").strip()
            dest_filter = dest if dest else None
            res = eng.generate_answer(q, destination_filter=dest_filter)
            print("\n" + "-" * 50)
            print(res["answer"])
            print("-" * 50)
        except (KeyboardInterrupt, EOFError):
            break


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--cli":
        run_cli()
    else:
        # Default run launches FastAPI server via Uvicorn
        uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
