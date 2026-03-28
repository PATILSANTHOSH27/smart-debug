import requests
import os
import re
import json

from app.models.schemas import (
    AnalyzeResponse, Issue, Scores, Breakdown, AnalysisMode
)

API_KEY = os.getenv("OPENROUTER_API_KEY")

def call_openrouter(prompt: str):
    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "model": "deepseek/deepseek-chat",
            "messages": [
                {"role": "user", "content": prompt}
            ]
        }
    )
    return response.json()


async def analyze_code(code: str, language: str, mode: AnalysisMode) -> AnalyzeResponse:
    try:
        prompt = f"""
        You are an expert code debugger.

        Return ONLY valid JSON. No text outside JSON.

        If JSON is invalid, response will be rejected.

        FORMAT:
        {{
          "issues": [
            {{"type": "error", "severity": "error", "message": "describe issue"}}
          ],
          "optimized_code": "fixed code here",
          "explanation": "clear explanation",
          "scores": {{
            "quality": 0,
            "performance": 0,
            "security": 0,
            "maintainability": 0
          }},
          "breakdown": {{
            "complexity": 0,
            "readability": 0,
            "best_practices": 0,
            "error_handling": 0
          }}
        }}

        CODE:
        {code}
        """

        data = call_openrouter(prompt)
        

        raw = data["choices"][0]["message"]["content"]

        try:
            json_text = re.search(r"\{.*\}", raw, re.DOTALL).group()
            parsed = json.loads(json_text)
        except:
            parsed = {
                "issues": [{"type": "info", "severity": "info", "message": raw}],
                "optimized_code": code,
                "explanation": raw,
                "scores": {"quality": 50, "performance": 50, "security": 50, "maintainability": 50},
                "breakdown": {"complexity": 50, "readability": 50, "best_practices": 50, "error_handling": 50}
            }

        return AnalyzeResponse(
            issues=[Issue(**issue) for issue in parsed.get("issues", [])],
            optimized_code=parsed.get("optimized_code", code),
            explanation=parsed.get("explanation", ""),
            scores=Scores(**parsed.get("scores", {})),
            breakdown=Breakdown(**parsed.get("breakdown", {}))
        )

    except Exception as e:
        return AnalyzeResponse(
            issues=[Issue(type="error", severity="error", message=str(e))],
            optimized_code=code,
            explanation="AI failed",
            scores=Scores(
                quality=50,
                performance=50,
                security=50,
                maintainability=50
            ),
            breakdown=Breakdown(
                complexity=50,
                readability=50,
                best_practices=50,
                error_handling=50
            )
        )
