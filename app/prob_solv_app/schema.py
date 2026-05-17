import operator
from typing import Annotated, List, Literal
from pydantic import BaseModel, Field
from typing_extensions import TypedDict
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, BaseMessage

# --- Step 1: Define the Persistent State ---
class AgentState(TypedDict):
    # The initial problem from the user
    original_query: str 
    # Student profile
    student_profile: str
    # Student id
    student_id: str
    # Category (Math/Writing)
    category: str
    # The structured list of steps to solve the problem
    plan_steps: List[str]
    # student input for current step
    student_input: str
    # Correct answers for each step
    correct_answers: Annotated[List[BaseMessage], operator.add]
    # Current index in the plan_steps list
    current_step_index: int
    # How many attempts the user has made for the current step
    attempts_left: int
    # Conversation history for context
    messages: Annotated[List[BaseMessage], operator.add]
    # Status to control flow
    status: Literal["classifying", "planning", "teaching", "finished"]
    # Summery of the lesson
    summery: str

# --- Step 2: Define Logic for Planner ---

# Pydantic model for structured output (The Plan)
class StepPlan(BaseModel):
    steps: List[str] = Field(description="A list of simple steps, sequential steps to solve the problem.")
