import requests
import os
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
        prompt = f"Analyze this {language} code:\n{code}"

        data = call_openrouter(prompt)
        result = data["choices"][0]["message"]["content"]

        return AnalyzeResponse(
            issues=[Issue(type="info", severity="info", message=result[:200])],
            optimized_code=code,
            explanation=result,
            scores=Scores(
                quality=80,
                performance=75,
                security=75,
                maintainability=80
            ),
            breakdown=Breakdown(
                complexity=75,
                readability=80,
                best_practices=75,
                error_handling=75
            )
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
