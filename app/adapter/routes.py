# app/api/init_llm.py
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, Literal

# own imports
from app.adapter.groq_ai import Groq_AIModelAdapter
from app.adapter.azureopenai import Azure_AIModelAdapter
from app.adapter.gemini_ai import Gemini_AIModelAdapter

router = APIRouter()

class LLMInitRequest(BaseModel):
    llm_name: Optional[str] = Literal["groq", "gemini", "azureopenai"] 
    temperature: float
    max_token: int

@router.post("/init-llm")
async def init_llm(llm_name, temp, max_tok, request: Request):
    print("Received init-llm request with params:", llm_name,temp, max_tok)
    if llm_name not in ["groq","gemini","azureopenai"]:
        return {"message": "Unsupported LLM"}
    try:
        if llm_name == "gemini":
            model = Gemini_AIModelAdapter(temperature=temp,max_tokens=max_tok)
            print("Gemini LLM model initialized in init-llm endpoint.")
            request.app.state.ai_model = model
            return JSONResponse(content={"message": "LLM initialized"}, status_code=200)
        elif llm_name == "groq":
            #model = Groq_AIModelAdapter(temperature=0.93,max_tokens=2048)
            model = Groq_AIModelAdapter(temperature=temp,max_tokens=max_tok)
            print("LLM model initialized in init-llm endpoint.")
            request.app.state.ai_model = model
            return JSONResponse(content={"message": "LLM initialized"}, status_code=200)
        elif llm_name == "azureopenai":
            #model = Groq_AIModelAdapter(temperature=0.93,max_tokens=2048)
            model = Azure_AIModelAdapter(temperature=temp,max_tokens=max_tok)
            print("LLM model initialized in init-llm endpoint.")
            request.app.state.ai_model = model
            return JSONResponse(content={"message": "Azure OpenAI LLM initialized"}, status_code=200)
    except Exception as e:
        return {"message": f"Failed to initialize LLM: {str(e)}"}
