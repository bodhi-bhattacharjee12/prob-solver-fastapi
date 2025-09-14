# app/api/init_llm.py
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional

# own imports
from app.adapter.groq_ai import Groq_AIModelAdapter

router = APIRouter()

class LLMInitRequest(BaseModel):
    llm_name: Optional[str] = "groq"
    temperature: float
    max_token: int

@router.post("/init-llm")
async def init_llm(llm_name, temp, max_tok, request: Request):
    print("Received init-llm request with params:", llm_name,temp, max_tok)
    if llm_name != "groq":
        return {"message": "Unsupported LLM"}
    try:
        #model = Groq_AIModelAdapter(temperature=0.93,max_tokens=2048)
        model = Groq_AIModelAdapter(temperature=temp,max_tokens=max_tok)
        print("LLM model initialized in init-llm endpoint.")
        request.app.state.ai_model = model
        return JSONResponse(content={"message": "LLM initialized"}, status_code=200)
        #return {"message": "LLM initialized"}
    except Exception as e:
        return {"message": f"Failed to initialize LLM: {str(e)}"}
