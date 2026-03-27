from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum


class AnalysisMode(str, Enum):
    DEBUG = "debug"
    OPTIMIZE = "optimize"
    EXPLAIN = "explain"
    REVIEW = "review"
    CONVERT = "convert"


class AnalyzeRequest(BaseModel):
    code: str = Field(..., min_length=1, description="The source code to analyze")
    language: str = Field(default="javascript", description="Programming language")
    mode: AnalysisMode = Field(default=AnalysisMode.DEBUG, description="Analysis mode")


class Issue(BaseModel):
    type: str = Field(default="error", description="Issue type: error, warning, info, performance")
    severity: str = Field(default="error", description="Severity level")
    message: str = Field(..., description="Human-readable description of the issue")


class Scores(BaseModel):
    quality: int = Field(default=0, ge=0, le=100)
    performance: int = Field(default=0, ge=0, le=100)
    security: int = Field(default=0, ge=0, le=100)
    maintainability: int = Field(default=0, ge=0, le=100)


class Breakdown(BaseModel):
    complexity: int = Field(default=0, ge=0, le=100)
    readability: int = Field(default=0, ge=0, le=100)
    best_practices: int = Field(default=0, ge=0, le=100)
    error_handling: int = Field(default=0, ge=0, le=100)


class AnalyzeResponse(BaseModel):
    issues: List[Issue] = []
    optimized_code: str = ""
    explanation: str = ""
    scores: Scores = Scores()
    breakdown: Breakdown = Breakdown()
