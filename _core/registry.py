from fastapi import FastAPI
from app.adapter.groq_ai import Groq_AIModelAdapter as AIModel
from app.adapter import _ai_model


def init_groq_ai(app: FastAPI):

    #global _ai_model # declear the _ai_model variable as global to modify it
    #if isinstance(_ai_model,AIModel)==False:
        try:
            app.state.ai_model = AIModel()
            global _ai_model
            _ai_model = app.state.ai_model
            if isinstance(_ai_model, AIModel) == False:
                raise ValueError("AI model is not initialized through startup.")
            print("Groq AI Model initialized.")
        except Exception as e:
            print(f"Failed to initialize Groq AI Model: {str(e)}")
            raise e
    #else:
    #    print("Groq AI Model already initialized.")

def get_ai_model() -> AIModel:
    """Get the initialized AI model."""
    if isinstance(_ai_model, AIModel) == False:
        print("get_ai_model in utility: ", type(_ai_model))
        raise ValueError("AI model is not initialized. inside registry.py")
    #ai_model = request.app.state.ai_model
    return _ai_model

