from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import JSONResponse
from fastapi import BackgroundTasks
from langgraph.graph.state import CompiledStateGraph

#own imports
#from app.vlog_creation.schema import VlogRequest, VlogResponse
from app.prob_solv_app.service import prob_solv_execution, generate_subpoint
from app.prob_solv_app.schema import AgentState, StepPlan
from app.adapter.groq_ai import Groq_AIModelAdapter
#from app.adapter.registry import get_ai_model
from app.prob_solv_app.dependencies import get_ai_model, get_orchestrator_worker, get_state_worker
from app.prob_solv_app.nodes import Nodes

router_ = APIRouter()


@router_.post("/test-llm")
async def use_llm(request: str, model: Groq_AIModelAdapter = Depends(get_ai_model)):
    try:
        result = model.chat(request)
        #return {"result": result}
        return JSONResponse(content={"message": result.content}, status_code=200)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router_.post("/initialize-graph")
async def graph_initialization(request: Request, model: Groq_AIModelAdapter = Depends(get_ai_model)):
    try:
        nodes = Nodes(model=model)  
        nodes.build_workflow()
        orchestrator_worker = nodes.compile_graph()
        request.app.state.orchestrator_worker = orchestrator_worker
        return JSONResponse(content={"message": "Graph initialized"}, status_code=200)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
## endpoint for generating sub points/steps for a math problem or writing task

@router_.post("/initial-graph-execution")
async def initial_graph_exec(request: Request, student_id: str, student_profile: str, problem_statement: str, orchestrator_worker: Nodes= Depends(get_orchestrator_worker)):
    try:
        question = generate_subpoint(request, student_id, student_profile, problem_statement, orchestrator_worker)
        return JSONResponse(content={"message": "Student needs to provide the answer for the question asked by AI teacher.", "Question": question}, status_code=200)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
## endpoint for generating sub points/steps for a math problem or writing task

@router_.post("/exec-prob-solve")
async def execute_prob_solver(request: Request, student_id: str, student_input: str, state: AgentState=Depends(get_state_worker), orchestrator_worker: CompiledStateGraph = Depends(get_orchestrator_worker)):
    """
    Endpoint to generate a vlog script using the AI model.
    """
    try:
        # Call the service function to generate the vlog
        response = prob_solv_execution(request, student_id, student_input, state, orchestrator_worker)
        #return response
        return JSONResponse(content={"message": response}, status_code=200)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except RuntimeError as re:
        raise HTTPException(status_code=500, detail=str(re))
    except Exception as e:
        print(f"Unexpected error in generate_sub_endpoint: {e}")
        raise HTTPException(status_code=444, detail=f'An unexpected error occurred.{e}')
    


