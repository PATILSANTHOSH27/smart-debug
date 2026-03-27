"""
AI Service — Google Gemini integration for code analysis.
Builds mode-specific prompts, calls Gemini, and parses structured JSON responses.
"""

import json
import os
import re
import google.generativeai as genai
from app.models.schemas import (
    AnalyzeResponse, Issue, Scores, Breakdown, AnalysisMode
)


# ---- Configure Gemini ----
_api_key = os.getenv("GEMINI_API_KEY","")
_model_name = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")

if _api_key:
    genai.configure(api_key=_api_key)


def _get_model():
    return genai.GenerativeModel(_model_name)


# ---- Prompt Templates ----

_SYSTEM_PROMPT = """You are an expert software engineer and code analyst.
You MUST respond with ONLY a valid JSON object — no markdown fences, no extra text.
The JSON must match this exact schema:

{
  "issues": [
    {"type": "<error|warning|info|performance>", "severity": "<error|warning|info>", "message": "<description>"}
  ],
  "optimized_code": "<the improved/fixed version of the code>",
  "explanation": "<detailed explanation of changes and reasoning>",
  "scores": {
    "quality": <0-100>,
    "performance": <0-100>,
    "security": <0-100>,
    "maintainability": <0-100>
  },
  "breakdown": {
    "complexity": <0-100>,
    "readability": <0-100>,
    "best_practices": <0-100>,
    "error_handling": <0-100>
  }
}
"""

_MODE_PROMPTS = {
    AnalysisMode.DEBUG: (
        "Analyze the following {language} code for BUGS and ERRORS. "
        "Identify all issues (logic errors, runtime errors, edge cases, type issues). "
        "Provide a corrected version in optimized_code and explain each fix."
    ),
    AnalysisMode.OPTIMIZE: (
        "Analyze the following {language} code for PERFORMANCE issues. "
        "Identify time/space complexity problems, redundant operations, and sub-optimal patterns. "
        "Provide an optimized version with better algorithmic complexity where possible."
    ),
    AnalysisMode.EXPLAIN: (
        "Explain the following {language} code in detail. "
        "Describe what each section does, the algorithm used, time/space complexity, "
        "and any noteworthy patterns. Put the explanation in the 'explanation' field. "
        "For optimized_code, return the same code with helpful inline comments added."
    ),
    AnalysisMode.REVIEW: (
        "Perform a thorough CODE REVIEW of the following {language} code. "
        "Check for: code style, best practices, error handling, naming conventions, "
        "potential bugs, security issues, and maintainability. "
        "Provide an improved version with all recommendations applied."
    ),
    AnalysisMode.CONVERT: (
        "The user wants to see this {language} code converted/improved. "
        "If it's JavaScript, convert to modern ES6+ with best practices. "
        "If it's Python 2 style, convert to Python 3 idioms. "
        "Apply modern language features and patterns. "
        "Explain the conversions in the explanation field."
    ),
}


def _build_prompt(code: str, language: str, mode: AnalysisMode) -> str:
    mode_instruction = _MODE_PROMPTS[mode].format(language=language)
    return f"{_SYSTEM_PROMPT}\n\n{mode_instruction}\n\nCode:\n```{language}\n{code}\n```"


# ---- JSON Parsing ----

def _extract_json(text: str) -> dict:
    """Robustly extract JSON from Gemini's response, handling markdown fences."""
    # Try to find JSON in code fences first
    fence_match = re.search(r'```(?:json)?\s*\n?(.*?)\n?```', text, re.DOTALL)
    if fence_match:
        text = fence_match.group(1).strip()

    # Try direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Try to find the first { ... } block
    brace_match = re.search(r'\{.*\}', text, re.DOTALL)
    if brace_match:
        try:
            return json.loads(brace_match.group())
        except json.JSONDecodeError:
            pass

    raise ValueError("Could not parse JSON from AI response")


def _clamp(val, lo=0, hi=100):
    """Clamp an integer to [lo, hi]."""
    try:
        return max(lo, min(hi, int(val)))
    except (TypeError, ValueError):
        return lo


# ---- Public API ----

async def analyze_code(code: str, language: str, mode: AnalysisMode) -> AnalyzeResponse:
    """Call Gemini to analyze code and return a structured response."""
    if not _api_key:
        raise RuntimeError(
            "GEMINI_API_KEY is not set. "
            "Create a .env file with GEMINI_API_KEY=your-key"
        )

    prompt = _build_prompt(code, language, mode)
    model = _get_model()

    try:
        response = model.generate_content(prompt)
        raw = response.text
    except Exception as exc:
        raise RuntimeError(f"Gemini API error: {exc}") from exc

    try:
        data = _extract_json(raw)
    except ValueError:
        # Fallback: return raw text as explanation
        return AnalyzeResponse(
            issues=[Issue(type="info", severity="info", message="AI returned non-structured response")],
            optimized_code=code,
            explanation=raw,
            scores=Scores(quality=50, performance=50, security=50, maintainability=50),
            breakdown=Breakdown(complexity=50, readability=50, best_practices=50, error_handling=50),
        )

    # Parse issues
    issues = []
    for item in data.get("issues", []):
        if isinstance(item, dict) and "message" in item:
            issues.append(Issue(
                type=item.get("type", "error"),
                severity=item.get("severity", item.get("type", "error")),
                message=item["message"],
            ))

    # Parse scores
    raw_scores = data.get("scores", {})
    scores = Scores(
        quality=_clamp(raw_scores.get("quality", 50)),
        performance=_clamp(raw_scores.get("performance", 50)),
        security=_clamp(raw_scores.get("security", 50)),
        maintainability=_clamp(raw_scores.get("maintainability", 50)),
    )

    # Parse breakdown
    raw_bd = data.get("breakdown", {})
    breakdown = Breakdown(
        complexity=_clamp(raw_bd.get("complexity", 50)),
        readability=_clamp(raw_bd.get("readability", 50)),
        best_practices=_clamp(raw_bd.get("best_practices", raw_bd.get("bestPractices", 50))),
        error_handling=_clamp(raw_bd.get("error_handling", raw_bd.get("errorHandling", 50))),
    )

    return AnalyzeResponse(
        issues=issues,
        optimized_code=data.get("optimized_code", data.get("optimizedCode", code)),
        explanation=data.get("explanation", ""),
        scores=scores,
        breakdown=breakdown,
    )
