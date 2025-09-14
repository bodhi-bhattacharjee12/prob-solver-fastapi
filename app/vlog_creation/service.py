#from app.adapter import ai_model
from fastapi import Request, Depends
from IPython.display import Markdown
from IPython.display import Image, display
from app.vlog_creation.dependencies import get_ai_model
from app.vlog_creation.nodes import Nodes
from app.adapter.groq_ai import Groq_AIModelAdapter

"""
def generate_vlog(llm_message:str) -> str:
    # Generate a vlog script using the AI model.
    ai_model = get_ai_model()
    if isinstance(ai_model,Groq_AIModelAdapter) == False:
        print("get_ai_model: ", type(ai_model))
        raise ValueError("AI model is not initialized in startup.")
    try:
        response = ai_model.chat(llm_message)
        print(response)
        return str(response.content)
    except Exception as e:
        raise RuntimeError(f"Failed to generate vlog: {str(e)}")
    """

def generate_vlog(llm_message:str, model: Groq_AIModelAdapter) -> str:
    """
    Generate a vlog script using the AI model.
    
    Args:
        llm_message (str): The message to send to the AI model.
        model (Groq_AIModelAdapter): The AI model adapter to use for generating the vlog.
    
    Returns:
        str: The generated vlog script.
    """
    try:
        #generate the instance for the node and create compile the graph
        nodes = Nodes(model=model)  
        nodes.build_workflow()
        orchestrator_worker = nodes.compile_graph()
        print("Invoking the workflow...")
        state = orchestrator_worker.invoke({"topic": llm_message})
        #print("Workflow completed.", state)
        #print(display(Image(orchestrator_worker.get_graph().draw_mermaid_png())))
        #return Markdown(state["final_report"])
        return state["final_report"] 
    except Exception as e:
        print(f"Error in generate_vlog: {e}")
        raise RuntimeError(f"Failed to generate vlog: {str(e)}")
