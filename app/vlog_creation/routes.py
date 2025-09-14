from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse

#own imports
#from app.vlog_creation.schema import VlogRequest, VlogResponse
from app.vlog_creation.service import generate_vlog
from app.adapter.groq_ai import Groq_AIModelAdapter
#from app.adapter.registry import get_ai_model
from app.vlog_creation.dependencies import get_ai_model

router_ = APIRouter()


@router_.post("/test-llm")
async def use_llm(request: str, model: Groq_AIModelAdapter = Depends(get_ai_model)):
    try:
        result = model.chat(request)
        #return {"result": result}
        return JSONResponse(content={"message": result}, status_code=200)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router_.post("/generate-vlog")
async def generate_vlog_endpoint(llm_message: str, model: Groq_AIModelAdapter = Depends(get_ai_model)):
    """
    Endpoint to generate a vlog script using the AI model.
    """
    try:
        # Call the service function to generate the vlog
        response = generate_vlog(llm_message, model=model)
        print("Response from generate_vlog:", response)
        #return response
        return JSONResponse(content={"message": response}, status_code=200)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except RuntimeError as re:
        raise HTTPException(status_code=500, detail=str(re))
    except Exception as e:
        print(f"Unexpected error in generate_vlog_endpoint: {e}")
        raise HTTPException(status_code=444, detail=f'An unexpected error occurred.{e}')


