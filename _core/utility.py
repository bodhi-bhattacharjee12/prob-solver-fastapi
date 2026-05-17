from fastapi import FastAPI, Request
import traceback
import sys
from fastapi.responses import JSONResponse
from fastapi.exception_handlers import http_exception_handler
from fastapi.exceptions import RequestValidationError

# our own imports
from app.prob_solv_app.schema import StepPlan
from app.adapter.groq_ai import Groq_AIModelAdapter
from app.adapter.gemini_ai import Gemini_AIModelAdapter
from app.adapter.azureopenai_old import Azure_AIModelAdapter


# define the planner function & get the same
def get_planner(llm):
    """Get the planner LLM."""
    if isinstance(llm, Groq_AIModelAdapter) or isinstance(llm, Gemini_AIModelAdapter) or isinstance(llm, Azure_AIModelAdapter):
        print("get_planner: ", type(llm))
    else:
        raise ValueError("Planner LLM is not initialized in startup.")
    
    # Augment the LLM with schema for structured output
    print("Getting planner from llm: ", type(llm))
    planner=llm.get_llm().with_structured_output(StepPlan)
    return planner
    

def register_exception_handlers(app: FastAPI):
    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        tb = traceback.TracebackException.from_exception(exc)
        stack_summary = "".join(tb.format())

        # Optional: log to console or file
        print(f"Unhandled Exception:\n{stack_summary}", file=sys.stderr)

        return JSONResponse(
            status_code=500,
            content={
                "error": str(exc),
                "type": exc.__class__.__name__,
                "trace": stack_summary
            }
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        return await http_exception_handler(request, exc)