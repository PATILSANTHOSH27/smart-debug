"""
Smart Debugger — FastAPI Backend
Serves the frontend as static files and exposes the /api/analyze endpoint.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# Load .env before anything else
load_dotenv()

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.models.schemas import AnalyzeRequest, AnalyzeResponse
from app.services.ai_service import analyze_code

# ---- App ----
app = FastAPI(
    title="Smart Debugger API",
    description="AI-powered code analysis backend",
    version="1.0.0",
)

# ---- CORS ----
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---- API Routes ----

@app.get("/api/health")
async def health_check():
    """Check if the server and AI provider are configured."""
    has_key = bool(os.getenv("GEMINI_API_KEY"))
    return {
        "status": "healthy",
        "ai_provider": "Google Gemini",
        "ai_configured": has_key,
        "model": os.getenv("GEMINI_MODEL", "gemini-2.0-flash"),
    }


@app.post("/api/analyze", response_model=AnalyzeResponse)
async def analyze(request: AnalyzeRequest):
    """Analyze code using AI and return structured results."""
    try:
        result = await analyze_code(
            code=request.code,
            language=request.language,
            mode=request.mode,
        )
        return result
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {exc}")


# ---- Serve Frontend ----
from fastapi.staticfiles import StaticFiles

app.mount("/", StaticFiles(directory="app/static", html=True), name="static")
