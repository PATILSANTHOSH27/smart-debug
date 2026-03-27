from groq import Groq
import os
from app.models.schemas import (
    AnalyzeResponse, Issue, Scores, Breakdown, AnalysisMode
)

client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def _build_prompt(code: str, language: str, mode: AnalysisMode) -> str:
    return f"""
You are an expert code analyzer.

Analyze the following {language} code based on mode: {mode}.

Return:
- List of issues
- Improved code
- Explanation

Code:
{code}
"""


async def analyze_code(code: str, language: str, mode: AnalysisMode) -> AnalyzeResponse:
    try:
        prompt = _build_prompt(code, language, mode)

        response = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        result = response.choices[0].message.content

        return AnalyzeResponse(
            issues=[Issue(
                type="info",
                severity="info",
                message=result[:200]  # short preview
            )],
            optimized_code=code,
            explanation=result,
            scores=Scores(
                quality=75,
                performance=70,
                security=70,
                maintainability=75
            ),
            breakdown=Breakdown(
                complexity=70,
                readability=75,
                best_practices=70,
                error_handling=70
            )
        )

    except Exception as e:
        return AnalyzeResponse(
            issues=[Issue(
                type="error",
                severity="error",
                message=str(e)
            )],
            optimized_code=code,
            explanation="AI service failed",
            scores=Scores(50, 50, 50, 50),
            breakdown=Breakdown(50, 50, 50, 50)
        )
