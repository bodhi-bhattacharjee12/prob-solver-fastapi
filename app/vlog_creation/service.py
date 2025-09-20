#from app.adapter import ai_model
from fastapi import Request, Depends
from IPython.display import Markdown
from IPython.display import Image, display
from langgraph.graph.state import CompiledStateGraph
from fastapi.encoders import jsonable_encoder

# own imports
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

def generate_vlog(llm_message:str, orchestrator_worker: CompiledStateGraph) -> str:
    """
    Generate a vlog script using the AI model.
    
    Args:
        llm_message (str): The message to send to the AI model.
        model (Groq_AIModelAdapter): The AI model adapter to use for generating the vlog.
    
    Returns:
        str: The generated vlog script.
    """
    try:
        print("Invoking the workflow...")

        # Thread metadata (optional) and initial input
        thread = {"configurable": {"thread_id": "5"}}
        initial_input = {"topic": llm_message}

        # Run the graph in streaming mode and inspect events
        states = orchestrator_worker.stream(initial_input, thread, stream_mode="values")
        print("stream() returned iterator of type:", type(states))

        for event in states:
            # Print diagnostic repr so we can see what's emitted
            print("Stream event repr:", repr(event))

            # If the event is a dict-like object
            if isinstance(event, dict):
                # sections could be present in the event
                if "sections" in event:
                    # Make sure the sections are JSON serializable before returning
                    serializable = jsonable_encoder(event["sections"])
                    print("Returning sections (jsonable):", serializable)
                    return serializable
                # final_report or other keys
                if "final_report" in event:
                    return jsonable_encoder(event["final_report"])

            # If the event has attribute 'state' or behaves like an object with .to_dict()
            try:
                state_attr = getattr(event, "state", None)
                if state_attr and isinstance(state_attr, dict) and "sections" in state_attr:
                    return jsonable_encoder(state_attr["sections"])
            except Exception:
                # ignore and continue
                pass

        # If stream completed without yielding sections, raise an error
        raise RuntimeError("Stream completed without producing 'sections'")
    except Exception as e:
        print(f"Error in generate_vlog: {e}")
        raise RuntimeError(f"Failed to generate vlog: {str(e)}")
