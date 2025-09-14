# app/api/init_llm.py
from fastapi import APIRouter, Request
from app.adapter.groq_ai import Groq_AIModelAdapter

router = APIRouter()


@router.post("/init-llm")
async def init_llm(llm_name,request: Request):
    if llm_name != "groq":
        return {"message": "Unsupported LLM"}
    try:
        model = Groq_AIModelAdapter()
        request.app.state.ai_model = model
        return {"message": "LLM initialized"}
    except Exception as e:
        return {"message": f"Failed to initialize LLM: {str(e)}"}   
