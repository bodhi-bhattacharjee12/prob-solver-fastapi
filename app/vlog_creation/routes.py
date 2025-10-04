from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import JSONResponse
from fastapi import BackgroundTasks

#own imports
#from app.vlog_creation.schema import VlogRequest, VlogResponse
from app.vlog_creation.service import generate_vlog, generate_subpoint
from app.vlog_creation.schema import Section, State
from app.adapter.groq_ai import Groq_AIModelAdapter
#from app.adapter.registry import get_ai_model
from app.vlog_creation.dependencies import get_ai_model, get_orchestrator_worker, get_state_worker
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
    
## endpoint for generating sub points
@router_.post("/generate-subpoints")
async def generate_sub_endpoint(request: Request, llm_message: str, orchestrator_worker: Nodes= Depends(get_orchestrator_worker)):
    """
    Endpoint to generate a vlog script using the AI model.
    """
    try:
        # Call the service function to generate the vlog
        response, unique_id = generate_subpoint(request, llm_message, orchestrator_worker)
        #return response
        return JSONResponse(content={"message": response, "unique_id": unique_id}, status_code=200)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except RuntimeError as re:
        raise HTTPException(status_code=500, detail=str(re))
    except Exception as e:
        print(f"Unexpected error in generate_sub_endpoint: {e}")
        raise HTTPException(status_code=444, detail=f'An unexpected error occurred.{e}')
    

## endpoint for generating vlog
@router_.post("/generate-vlog")
async def generate_vlog_endpoint(unique_id: str, human_review: list[Section], state: State =Depends(get_state_worker), orchestrator_worker: Nodes= Depends(get_orchestrator_worker)):
    """
    Endpoint to generate a vlog script using the AI model.
    """
    try:
        # Call the service function to generate the vlog
        print("Human review received in endpoint generate_vlog_endpoint")
        response = generate_vlog(human_review, state[unique_id], orchestrator_worker)
        #return response
        return JSONResponse(content={"message": response}, status_code=200)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except RuntimeError as re:
        raise HTTPException(status_code=500, detail=str(re))
    except Exception as e:
        print(f"Unexpected error in generate_vlog_endpoint: {e}")
        raise HTTPException(status_code=444, detail=f'An unexpected error occurred.{e}')


