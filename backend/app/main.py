"""
Smart Debugger — FastAPI Backend
Serves the frontend as static files and exposes the /api/analyze endpoint.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# Load .env before anything else
load_dotenv(dotenv_path=Path(__file__).parent / ".env")

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from models.schemas import AnalyzeRequest, AnalyzeResponse
from services.ai_service import analyze_code

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
_frontend_dir = Path(__file__).parent.parent / "frontend"

if _frontend_dir.is_dir():
    # Serve static assets (CSS, JS, images)
    app.mount("/static", StaticFiles(directory=str(_frontend_dir)), name="static")

    @app.get("/style.css")
    async def serve_css():
        return FileResponse(_frontend_dir / "style.css", media_type="text/css")

    @app.get("/script.js")
    async def serve_js():
        return FileResponse(_frontend_dir / "script.js", media_type="application/javascript")

    @app.get("/")
    async def serve_index():
        return FileResponse(_frontend_dir / "index.html")

    # Catch-all for SPA-like routing (return index.html for unknown paths)
    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        file_path = _frontend_dir / full_path
        if file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(_frontend_dir / "index.html")
