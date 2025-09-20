from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import JSONResponse

#own imports
#from app.vlog_creation.schema import VlogRequest, VlogResponse
from app.vlog_creation.service import generate_vlog
from app.adapter.groq_ai import Groq_AIModelAdapter
#from app.adapter.registry import get_ai_model
from app.vlog_creation.dependencies import get_ai_model, get_orchestrator_worker
from app.vlog_creation.nodes import Nodes

router_ = APIRouter()


@router_.post("/test-llm")
async def use_llm(request: str, model: Groq_AIModelAdapter = Depends(get_ai_model)):
    try:
        result = model.chat(request)
        #return {"result": result}
        return JSONResponse(content={"message": result}, status_code=200)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router_.post("/initialize-graph")
async def generate_vlog_endpoint(request: Request, model: Groq_AIModelAdapter = Depends(get_ai_model)):
    try:
        nodes = Nodes(model=model)  
        nodes.build_workflow()
        orchestrator_worker = nodes.compile_graph()
        request.app.state.orchestrator_worker = orchestrator_worker
        return JSONResponse(content={"message": "Graph initialized"}, status_code=200)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
## endpoint for generating vlog
@router_.post("/generate-vlog")
async def generate_vlog_endpoint(llm_message: str, orchestrator_worker: Nodes= Depends(get_orchestrator_worker)):
    """
    Endpoint to generate a vlog script using the AI model.
    """
    try:
        # Call the service function to generate the vlog
        response = generate_vlog(llm_message, orchestrator_worker)
        #return response
        return JSONResponse(content={"message": response}, status_code=200)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except RuntimeError as re:
        raise HTTPException(status_code=500, detail=str(re))
    except Exception as e:
        print(f"Unexpected error in generate_vlog_endpoint: {e}")
        # Log the orchestrator_worker type for debugging
        try:
            print("orchestrator_worker type:", type(orchestrator_worker))
        except Exception:
            pass
        raise HTTPException(status_code=500, detail=f'An unexpected error occurred.{e}')


