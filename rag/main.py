"""
FastAPI Server for Vector-Based RAG
====================================
Replaces Streamlit UI with REST API endpoints.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import os
import tempfile
from pathlib import Path
from dotenv import load_dotenv
from rag_pipeline import VectorRAG

load_dotenv()

# Global RAG instance
rag_instance: Optional[VectorRAG] = None

# ════════════════════════════════════════════════════════════════════════════════
# PYDANTIC MODELS (Request/Response schemas)
# ════════════════════════════════════════════════════════════════════════════════

class QueryRequest(BaseModel):
    question: str

class SourceInfo(BaseModel):
    label: str
    doc_id: str
    page_num: int
    chunk_index: int
    score: float
    preview: str

class QueryResponse(BaseModel):
    question: str
    answer: str
    sources: List[SourceInfo]
    retrieved: List[SourceInfo]

class IngestionStats(BaseModel):
    files: int
    pages: int
    chunks: int

class HealthResponse(BaseModel):
    status: str
    message: str

class StatsResponse(BaseModel):
    total_documents: int | str

# ════════════════════════════════════════════════════════════════════════════════
# FASTAPI STARTUP/SHUTDOWN
# ════════════════════════════════════════════════════════════════════════════════

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize RAG on startup, cleanup on shutdown."""
    global rag_instance
    
    print("🚀 Initializing RAG System...")
    try:
        rag_instance = VectorRAG(
            persist_dir="./chroma_db",
            google_api_key=os.environ.get("GOOGLE_API_KEY"),
            hf_api_key=os.environ.get("HUGGINGFACE_API_KEY"),
        )
        print("✓ RAG System Ready")
    except Exception as e:
        print(f"✗ RAG Initialization Failed: {e}")
        raise
    
    yield
    
    print("🛑 Shutting down...")

# ════════════════════════════════════════════════════════════════════════════════
# CREATE FASTAPI APP
# ════════════════════════════════════════════════════════════════════════════════

app = FastAPI(
    title="Meridian RAG API",
    description="Vector-based RAG for policy documents (replacing Streamlit UI)",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware (allow cross-origin requests)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ════════════════════════════════════════════════════════════════════════════════
# ROOT & HEALTH ENDPOINTS
# ════════════════════════════════════════════════════════════════════════════════

@app.get("/")
async def root():
    """Welcome message with API documentation."""
    return {
        "name": "Meridian RAG API",
        "version": "1.0.0",
        "description": "FastAPI replacement for Streamlit RAG UI",
        "docs": "http://localhost:8000/docs",
        "swagger_ui": "http://localhost:8000/swagger_ui",
        "endpoints": {
            "GET /health": "Health check status",
            "POST /api/query": "Query the RAG pipeline",
            "POST /api/ingest": "Upload and index documents",
            "GET /api/stats": "Get database statistics"
        }
    }

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint - shows RAG system status."""
    if rag_instance:
        return {"status": "ready", "message": "RAG system initialized"}
    return {"status": "initializing", "message": "RAG system still loading"}

# ════════════════════════════════════════════════════════════════════════════════
# RAG ENDPOINTS
# ════════════════════════════════════════════════════════════════════════════════

@app.post("/api/query", response_model=QueryResponse)
async def query_documents(request: QueryRequest):
    """
    Query the RAG pipeline for document-based answers.
    
    This endpoint:
    1. Takes a question
    2. Retrieves relevant document chunks from vectorstore
    3. Sends them to Gemini LLM
    4. Returns answer with cited sources
    
    Example:
        POST /api/query
        {"question": "What is the ambient pallet storage rate?"}
    
    Response:
        {
            "question": "...",
            "answer": "...",
            "sources": [...],
            "retrieved": [...]
        }
    """
    if not rag_instance:
        raise HTTPException(status_code=500, detail="RAG system not initialized")
    
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")
    
    try:
        result = rag_instance.query(request.question)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Query failed: {str(e)}")


@app.post("/api/ingest", response_model=IngestionStats)
async def ingest_documents(files: List[UploadFile] = File(...)):
    """
    Upload and index new documents into the vector database.
    
    This endpoint:
    1. Receives uploaded document files (PDF, DOCX, XLSX, TXT)
    2. Saves them temporarily
    3. Extracts text and splits into chunks
    4. Generates embeddings for each chunk
    5. Stores in Chroma vectorstore
    6. Cleans up temporary files
    
    Supported formats: PDF, DOCX, XLSX, XLS, TXT
    
    Example:
        POST /api/ingest
        files: [policy.pdf, data.xlsx, emails.docx]
    
    Response:
        {
            "files": 3,
            "pages": 45,
            "chunks": 284
        }
    """
    if not rag_instance:
        raise HTTPException(status_code=500, detail="RAG system not initialized")
    
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")
    
    # Validate file types
    allowed_extensions = {".pdf", ".docx", ".xlsx", ".xls", ".txt"}
    
    # Save uploaded files to temporary directory
    temp_dir = Path(tempfile.gettempdir()) / "rag_uploads"
    temp_dir.mkdir(exist_ok=True)
    
    file_paths = []
    try:
        for uploaded_file in files:
            if not uploaded_file.filename:
                continue
            
            # Check file extension
            file_ext = Path(uploaded_file.filename).suffix.lower()
            if file_ext not in allowed_extensions:
                raise HTTPException(
                    status_code=400,
                    detail=f"File type {file_ext} not supported. Allowed: {', '.join(allowed_extensions)}"
                )
            
            temp_path = temp_dir / uploaded_file.filename
            contents = await uploaded_file.read()
            temp_path.write_bytes(contents)
            file_paths.append(str(temp_path))
        
        if not file_paths:
            raise HTTPException(status_code=400, detail="No valid files to ingest")
        
        # Ingest documents into vectorstore
        print(f"[API] Ingesting {len(file_paths)} file(s)...")
        stats = rag_instance.ingest(file_paths)
        
        # Cleanup temporary files
        for fp in file_paths:
            try:
                Path(fp).unlink()
            except:
                pass
        
        return stats
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Ingestion failed: {str(e)}")


@app.get("/api/stats", response_model=StatsResponse)
async def get_stats():
    """
    Get vector database statistics.
    
    Returns:
        {
            "total_documents": number of chunks indexed
        }
    """
    if not rag_instance:
        raise HTTPException(status_code=500, detail="RAG system not initialized")
    
    try:
        stats = rag_instance.get_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not retrieve stats: {str(e)}")


# ════════════════════════════════════════════════════════════════════════════════
# CUSTOM ERROR HANDLERS
# ════════════════════════════════════════════════════════════════════════════════

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle unexpected errors gracefully."""
    return {
        "error": str(exc),
        "status": "error"
    }


# ════════════════════════════════════════════════════════════════════════════════
# RUN SERVER
# ════════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)