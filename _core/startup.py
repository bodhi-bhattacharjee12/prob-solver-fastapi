from fastapi import FastAPI
from fastapi import Request, Depends
from app.adapter.groq_ai import Groq_AIModelAdapter as AIModel
from app.adapter import _ai_model
#import app.adapter as adapter

"""
def register_startup_event(app: FastAPI):
    @app.on_event("startup")
    async def startup_event():
        print("Initializing AIModel from startup module...")
        from app.adapter import ai_model
        #ai_model = AIModel()
        #return ai_model
        """




