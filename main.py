from fastapi import FastAPI
from app.prob_solv_app.routes import router_ as vlog_router
from app.prob_solv_app.routes import router_
from _core.registry import init_groq_ai
from _core.utility import register_exception_handlers
from contextlib import asynccontextmanager
from app.adapter.routes import router as init_router
from app.prob_solv_app.routes import router_ as use_router


#register_startup_event(app)  # 👈 You pass the app here
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting up AI model...")
    #init_groq_ai(app)   # Initialize here
    yield
    print("Shutting down AI model...")

app = FastAPI(
    title="GenAI Problem Solver APP",
    lifespan=lifespan,
    description="An app to help solving problems for the specially abled students using agentic AI",
    version="1.0.0"
)

# Include the vlog creation routes
app.include_router(vlog_router, prefix="/prob_solver", tags=["Problem Solver"])

# Pass app to your router factory
#router = get_router(app)
app.include_router(router_)
app.include_router(init_router)
app.include_router(use_router)


# register the exception handlers
register_exception_handlers(app)


# Root endpoint
@app.get("/")
def read_root():
    return {"message": "Welcome to the GenAI Problem Solver API"}