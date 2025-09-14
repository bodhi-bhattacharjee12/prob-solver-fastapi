from fastapi import FastAPI
from app.vlog_creation.routes import router_ as vlog_router
from app.vlog_creation.routes import router_
from _core.registry import init_groq_ai
from _core.utility import register_exception_handlers
from contextlib import asynccontextmanager
from app.adapter.routes import router as init_router
from app.vlog_creation.routes import router_ as use_router


#register_startup_event(app)  # 👈 You pass the app here
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting up AI model...")
    #init_groq_ai(app)   # Initialize here
    yield
    print("Shutting down AI model...")

app = FastAPI(
    title="GenAI Vlog Creation API",
    lifespan=lifespan,
    description="An API to generate vlogs using GenAI adapters",
    version="1.0.0"
)

# Include the vlog creation routes
app.include_router(vlog_router, prefix="/vlog", tags=["Vlog Creation"])

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
    return {"message": "Welcome to the GenAI Vlog Creation API"}