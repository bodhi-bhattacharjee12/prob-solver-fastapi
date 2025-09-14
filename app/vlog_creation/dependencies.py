from fastapi import Request
from app.adapter.groq_ai import Groq_AIModelAdapter

## Dependencies injection for the AI model
# This module provides a dependency to access the AI model instance in FastAPI routes.

def get_ai_model(request: Request) -> Groq_AIModelAdapter:
    model = request.app.state.ai_model
    if not model:
        raise RuntimeError("LLM not initialized")
    return model
