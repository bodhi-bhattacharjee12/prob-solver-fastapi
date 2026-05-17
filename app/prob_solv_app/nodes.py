import json
from tkinter import END
from fastapi import Depends, Request
from langgraph.types import Send
from typing_extensions import TypedDict
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage,SystemMessage,AIMessage
from langgraph.types import interrupt, Command
from langgraph.checkpoint.memory import MemorySaver,InMemorySaver

from app.prob_solv_app.schema import AgentState, StepPlan
from app.prob_solv_app.dependencies import get_ai_model
from app.adapter.groq_ai import Groq_AIModelAdapter
from app.prob_solv_app.prompt import classifier_prompt, get_planner_prompt,get_summery_prompt,get_student_prompt,get_validation_prompt, get_ans_from_teacher_prompt
from _core.utility import get_planner
from _core.registry import get_ai_model


#global student_input_data 
student_input_data = {}
#global messages
messages = []
#global attempts
attempts = 3

# Nodes for the graph
class Nodes:

    #def __init__(self, request: Request ,model: Groq_AIModelAdapter = Depends(get_ai_model)):
    def __init__(self, model: Groq_AIModelAdapter):
        # Get the planner and LLM from the registry
        self.llm = model.get_llm()
        self.planner = get_planner(model)

    def _get_field(self, obj, field):
        """Safely get a field from a dict-like or object-like state."""
        try:
            if isinstance(obj, dict):
                print(f"topic {field} is in dict")
                return obj.get(field)
            print(f"topic {field} is in object")
            return getattr(obj, field, None)
        except Exception as e:
            return e
        
    # define classifier node    
    def classifier_node(self, state: AgentState):
        """Determines if the problem is Math or Writing."""
        query = self._get_field(state, 'original_query')
        print(f"--- Classifying: {query} ---")

        # Use the imported classifier_prompt
        chain = classifier_prompt | self.llm
        category = chain.invoke({"query": query}).content.strip().lower()
        
        # Normalize category
        cat = "math" if "math" in category else "writing"
        return {"category": cat, "status": "planning"}
    # end of classifier node

    # define the planner node
    def planner_node(self, state: AgentState):
        """Breaks the problem into a structured list of steps."""
        print("--- Planning Steps ---")
        category = self._get_field(state,'category')
        query = self._get_field(state,'original_query')
        student_profile = self._get_field(state,'student_profile')
        
        # Configure structured output for the LLM
        structured_llm = self.llm.with_structured_output(StepPlan)

        response = structured_llm.invoke([
            SystemMessage(content=get_planner_prompt(category, student_profile)),
            HumanMessage(content=query)
        ])

        try:
            print(f"Planned Steps: {response}")
            # validate the planned steps is a list of strings
            plan = StepPlan.model_validate(response)
        except Exception as e:
            raise RuntimeError(f"Error printing planned steps: {e}") 
        
        # Initialize the teaching state
        global attempts
        attempts = 3
        return {
            "plan_steps": plan.steps,
            "current_step_index": 0,
            "attempts_left": attempts,
            "status": "teaching",
            "messages": [AIMessage(content=f"I have broken this down into {len(plan.steps)} steps. Let's start with step 1!, {plan.steps[0]}")]
        }
    # end of planner node

    # Refactored Teacher Node
    def teacher_node(self, state: AgentState):
        """
        Refactored Teacher Node: No internal loops. 
        Relies on 'current_step_index' and 'attempts_left' to track progress.
        """
        print("--- Teacher Agent Active ---")       
        try:
            # 1 GET STATE (This is your persistent memory)
            steps = self._get_field(state, 'plan_steps')
            idx = self._get_field(state, 'current_step_index')
            attempts = self._get_field(state, 'attempts_left')
            messages = self._get_field(state, 'messages') or []
            #student_input_data = self._get_field(state, 'student_input') or None
            current_step_content = steps[idx] if idx < len(steps) else None
            correct_answers = self._get_field(state, 'correct_answers') or []
            student_profile = self._get_field(state, 'student_profile')
            cat = self._get_field(state, 'category')

            # 2. CHECK IF ALL STEPS ARE DONE
            if idx >= len(steps):
                # gather all previous messages content together in a single string
                #all_messages = "\n".join([msg.content for msg in messages])
                # Generate summary based on the history of messages
                # (Assuming you want to summarize the interaction)
                summary_prompt = get_summery_prompt(steps,correct_answers)
                try:
                    summary = self.llm.invoke([
                        SystemMessage(content="You are a helpful teacher."), 
                        HumanMessage(content=summary_prompt)
                    ])
                    return {"messages": [summary], "status": "finished"}
                except Exception as e:
                    print("Error generating summary:", e)
                    return {"messages": [AIMessage(content="The lesson is completed successfully. Go ahead with the next problem.")], "status": "finished"}
            
            # Generate the question for this step
            # (It's okay to regenerate this on re-entry, or you could store it in state)
            if (isinstance(messages[-1], AIMessage)) and attempts == 3:
                # =========================================================
                # 3. POSE THE QUESTION/HINT
                question = self.llm.invoke(get_student_prompt(cat,current_step_content, steps[:idx], correct_answers)).content
                messages.append(AIMessage(content=question))

                # =========================================================
                # 4. THE PAUSE (Interrupt)
                # =========================================================
                # The graph stops here. When it resumes, 'student_input_data' 
                # will contain the data you sent in 'Command(resume={...})'
                print("Interrupting to get student input for question:", messages[-1].content)
                return {"messages": messages, "current_step_index": idx, "attempts_left": attempts,"status":"teaching"}

            elif isinstance(messages[-1], HumanMessage):
                # =========================================================
                # 5. THE RESUME (Logic runs only after user answers)
                # =========================================================
                student_input_data = messages[-1].content
                if cat != "math":
                    student_input_data = student_input_data[:400]  # enforce char limit for writing
                input_data = get_validation_prompt(cat, student_input_data, current_step_content)
                print("Resumed with input:", input_data)
            
                # Validate Logic
                val_response = self.llm.invoke(input_data).content
                print("Validation response:", val_response)
                if "||" in val_response:
                    status_code, feedback = val_response.split("||", 1)
                else:
                    status_code = "INCORRECT"
                    feedback = val_response
                    
                status_code = status_code.strip().upper()

                # 6. DETERMINE NEXT STATE
                # We return a dictionary update. LangGraph merges this into AgentState.
                
                if status_code == "CORRECT":
                    # SUCCESS: Move index forward, reset attempts
                    success_msg = f"{feedback.strip()} Moving on."
                    print(success_msg)
                    if cat == "math":
                        correct_answers.append(student_input_data)
                    else:
                        correct_answers.append(feedback.strip())
                    if idx+1 >= len(steps):
                        # Generate summary based on the history of messages
                        # (Assuming you want to summarize the interaction)
                        messages.append(AIMessage(content=success_msg))
                        # get all previous messages content together in a single string
                        #all_messages = "\n".join([msg.content for msg in messages])
                        summary_prompt = get_summery_prompt(steps,correct_answers)
                        try:
                            summary = self.llm.invoke([
                                SystemMessage(content="You are a helpful teacher."), 
                                HumanMessage(content=summary_prompt)
                            ])
                            return {"messages": [summary], "status": "finished"}
                        except Exception as e:
                            print("Error generating summary:", e)
                            return {"messages": [AIMessage(content="The lesson is completed successfully. Go ahead with the next problem.")], "status": "finished"}

                    current_step_content = steps[idx+1]
                    question = self.llm.invoke(get_student_prompt(cat, current_step_content, steps[:idx], correct_answers)).content
                    next_step = AIMessage(content=(success_msg + f"\nNow, please solve the following step: {question}"))
                    messages.append(next_step)
                    attempts = 3
                    return {
                        "messages": messages, # Append history
                        "current_step_index": idx+1,  # <--- This acts as the 'next' in your for loop
                        "attempts_left": attempts,       # <--- Reset for next step
                        "status": "teaching",
                        "correct_answers": correct_answers
                    }
                else:
                    # FAILURE: Decrease attempts, keep index same
                    attempts = attempts - 1
                    
                    if attempts > 0:
                        # RETRY: The graph will re-run this node, see the same 'idx', but lower 'attempts'
                        fail_msg = AIMessage(content=f"Not quite. {feedback.strip()} ({attempts} tries left).")
                        messages.append(fail_msg)
                        # return with Fail message and decremented attempts
                        print(fail_msg.content)
                        return {
                        "messages": messages, # Append history
                        "attempts_left": attempts,       # <--- Reset for next step
                        "status": "teaching"
                    }
                    else:
                        # EXHAUSTED: Reveal answer, force move forward
                        correct_ans = self.llm.invoke(get_ans_from_teacher_prompt(cat, student_profile, current_step_content, steps[:idx], correct_answers)).content
                        print("Your attempt exausted. The correct answer is:", correct_ans)
                        tough_msg = f"That was tough! The answer was: {correct_ans}. Let's move on."
                        correct_answers.append(correct_ans)
                        if idx+1 >= len(steps):
                            messages = messages.append(AIMessage(content=tough_msg))
                            # get all previous messages content together in a single string
                            #all_messages = "\n".join([msg.content for msg in messages])
                            # Generate summary based on the history of messages
                            # (Assuming you want to summarize the interaction)
                            summary_prompt = get_summery_prompt(steps,correct_answers)
                            try:
                                summary = self.llm.invoke([
                                    SystemMessage(content="You are a helpful teacher."), 
                                    HumanMessage(content=summary_prompt)
                                ])
                                return {"messages": [summary], "status": "finished"}
                            except Exception as e:
                                print("Error generating summary:", e)
                                return {"messages": [AIMessage(content="The lesson is completed successfully. Go ahead with the next problem.")], "status": "finished"}
                        current_step_content = steps[idx+1]
                        question = self.llm.invoke(get_student_prompt(cat, current_step_content, steps[:idx], correct_answers)).content
                        next_step = AIMessage(content=(tough_msg + f"\nNow, please solve the next step: {question}"))
                        messages.append(next_step)                    
                        attempts = 3
                        return {
                            "messages": messages,
                            "current_step_index": idx + 1, # <--- Force next step
                            "attempts_left": attempts
                        }
        except Exception as e:
            raise RuntimeError("Teacher node with error in : " + str(e))
        # end of teacher node
    
    # Define the Dummy Node
    def student_interrupt_node(self, state: AgentState):
        """
        This node does NOTHING. It exists solely to be the 'Interrupt Point'.
        When we resume, we will effectively skip past this or run it as a pass-through.
        """
        print("--- Entering Student Node (Should Pause Before This) ---")
        return {}
            
    def build_workflow(self):
        """Build the workflow graph"""

        from langgraph.graph import StateGraph, START, END
        #from IPython.display import Image, display
        self.orchestrator_worker_builder = StateGraph(AgentState)

        # Add the nodes
        self.orchestrator_worker_builder.add_node("classifier", self.classifier_node)
        self.orchestrator_worker_builder.add_node("planner", self.planner_node)
        self.orchestrator_worker_builder.add_node("teacher", self.teacher_node)
        self.orchestrator_worker_builder.add_node("student_interrupt", self.student_interrupt_node)

        # Add edges to connect nodes
        self.orchestrator_worker_builder.add_edge(START, "classifier")
        self.orchestrator_worker_builder.add_edge("classifier", "planner")
        self.orchestrator_worker_builder.add_edge("planner", "teacher")
        #self.orchestrator_worker_builder.add_edge("teacher", END)
        
        ## student input interrupt node
        def graph_router(state:AgentState):
            print("Student interruption node reached. Current state:",state["status"])
            if state.get("status") == "finished":
                return END
            else:
                return "student_interrupt"  # Loop back to itself!
        
        self.orchestrator_worker_builder.add_conditional_edges("teacher", graph_router, {"student_interrupt": "student_interrupt", END: END})
        # Student always goes back to Teacher to process the input
        self.orchestrator_worker_builder.add_edge("student_interrupt", "teacher")

    def compile_graph(self):
        """Compile the graph and return the workflow"""
        try:
            self.build_workflow()
            memory=InMemorySaver()
            self.orchestrator_worker = self.orchestrator_worker_builder.compile(checkpointer=memory,interrupt_before=["student_interrupt"])
            print("grapg compilation is successful",type(self.orchestrator_worker))
            return self.orchestrator_worker
        except Exception as e:
            print(f"Error compiling graph: {e}")
            raise RuntimeError("Failed to compile the workflow graph") from e
