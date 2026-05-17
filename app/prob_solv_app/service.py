#from app.adapter import ai_model
import uuid
from fastapi import Request, Depends
#from IPython.display import Markdown
#from IPython.display import Image, display
from langgraph.graph.state import CompiledStateGraph, Command
from langchain_core.messages import HumanMessage,SystemMessage,AIMessage
from fastapi.encoders import jsonable_encoder

# own imports
from app.prob_solv_app.dependencies import get_ai_model
from app.prob_solv_app.nodes import Nodes
from app.prob_solv_app.dependencies import get_orchestrator_worker, get_state_worker,get_ai_model
#from app.adapter.groq_ai import Groq_AIModelAdapter
from app.prob_solv_app.schema import StepPlan, AgentState


def generate_subpoint(request: Request, student_id:str, student_profile:str, llm_message:str, orchestrator_worker: CompiledStateGraph) -> str:
    """
    Generate the subpoints for the problem into multiple steps using the AI model, so that each step can be taught individually.
    
    Args:
        llm_message (str): The message to send to the AI model.
        model (Groq_AIModelAdapter): The AI model adapter to use for generating the vlog.
    
    Returns:
        str: The generated vlog script.
    """
    try:
        print("Invoking the workflow...")

        # Thread metadata (optional) and initial input
        thread = {"configurable": {"thread_id": student_id}}
        # 2. Define Initial State
        initial_input = {
            "original_query": llm_message,
            "student_profile": student_profile,
            "student_id": student_id,
            "category": "",
            "plan_steps": [],
            "current_step_index": 0,
            "attempts_left": 3,
            "messages": [], 
            "status": "classifying"
        }
        
        # Run the graph in streaming mode and inspect events
        #states = orchestrator_worker.stream(initial_input, thread, stream_mode="values")

        # If the event has attribute 'state' or behaves like an object with .to_dict()
        try:
            # 4. Invoke Graph
            # The graph will run Classifier -> Planner -> Teacher -> INTERRUPT
            # It will pause automatically when it hits 'interrupt()' in the teacher node.
            states = orchestrator_worker.invoke(initial_input, config=thread)
            #states = orchestrator_worker.stream(initial_input, thread, stream_mode="values")
            print("invoke() returned iterator of type:", type(states))
        
            #for event in states:
            if isinstance(states, dict):
                # messages could be present in the event
                if "messages" in states:
                    # Make sure the sections are JSON serializable before returning
                    if isinstance(states["messages"][-1], AIMessage):
                        print("Final AI Message to student:", states["messages"][-1].content)
                        serializable = jsonable_encoder(states["messages"][-1].content)
                        request.app.state.state= dict()
                        request.app.state.state = states # Store the state in the app state
                        return serializable
            else:
                state_attr = getattr(states, "state", None)
                if state_attr and isinstance(state_attr, dict) and "messages" in state_attr:
                    request.app.state.state= dict()
                    request.app.state.state = states # Store the state in the app state
                    if isinstance(state_attr["messages"][-1], AIMessage):
                        print("Final initial workflow AI Message to student:", state_attr["messages"][-1].content)
                        return jsonable_encoder(state_attr["messages"][-1].content)
                    else:
                        print("Initial message is not an AIMessage.")
                        return jsonable_encoder(state_attr["messages"][-1].content)
                    
        except Exception as e:
            # Handle exceptions that occur during invocation
            raise RuntimeError("graph invoked with error: " + str(e))
    except Exception as e:
        print(f"Error in invoking the initial workflow: {e}")
        raise RuntimeError(f"Failed to generate subpoints: {str(e)}")
    

def prob_solv_execution(request: Request, student_id: str, student_input: str, state: AgentState, orchestrator_worker: CompiledStateGraph) -> str:
    """
    Step by step execution of the problem solving process.
    
    Args:
        student_input (str): The input from the student.
        model (Groq_AIModelAdapter): The AI model adapter to use for generating the vlog.
    
    Returns:
        str: The generated vlog script.
    """
    try:
        print("Invoking the workflow again after student input..")
        # update the section field of of the Status which got generated out of orchestrator_worker in the previous api call
        #state['sections'] = human_review
        print("Got student input:", student_input)
        # Thread metadata (optional) and initial input
        thread = {"configurable": {"thread_id": student_id}}
        # get the state from the app state
        #state = request.app.state.state.get(student_id)
        # Update the state with the student input
        state['student_input'] = student_input
        state['messages']= [HumanMessage(content=student_input)]
        # save the state in the request app state
        request.app.state.state = state
        
        # update the state in the app state
        orchestrator_worker.update_state(thread, state, as_node="student_interrupt")

        try:
            # Use invoke for simplicity in REST APIs
            #command = Command(resume={"student_input": student_input})
            #result = orchestrator_worker.invoke(command, config=thread)
            states = orchestrator_worker.invoke(None, config=thread)
        
            #for event in states:
            if isinstance(states, dict):
                # messages could be present in the event
                if "messages" in states:
                    # Make sure the sections are JSON serializable before returning
                    if isinstance(states["messages"][-1], AIMessage):
                        print("Message to student:", states["messages"][-1].content)
                        serializable = jsonable_encoder(states["messages"][-1].content)
                        request.app.state.state= dict()
                        request.app.state.state = states # Store the state in the app state
                        if states["status"] == "finished":
                            #print("Final state after finishing all steps:", states)
                            last_msg_feedback = jsonable_encoder(states["messages"][-2].content)  
                            return last_msg_feedback + "\n\n" + serializable
                        return serializable
            else:
                state_attr = getattr(states, "state", None)
                if state_attr and isinstance(state_attr, dict) and "messages" in state_attr:
                    request.app.state.state= dict()
                    request.app.state.state = states # Store the state in the app state
                    if isinstance(state_attr["messages"][-1], AIMessage):
                        print("Message to student:", state_attr["messages"][-1].content)
                        if states["status"] == "finished":
                            #print("Final state after finishing all steps:", states)
                            last_msg_feedback = jsonable_encoder(state_attr["messages"][-2].content + "\n\n" + state_attr["messages"][-1].content)  
                            return last_msg_feedback
                        return jsonable_encoder(state_attr["messages"][-1].content)
                    else:
                        print("Final message is not an AIMessage.")
                        return jsonable_encoder(state_attr["messages"][-1].content)

        except Exception as e:
            # Handle exceptions that occur during invocation
            raise RuntimeError("graph invoked with error in : " + str(e))

    except Exception as e:
        print(f"Error in prob_solv_execution: {e}")
        raise RuntimeError(f"Failed to prob_solv_execution: {str(e)}")

