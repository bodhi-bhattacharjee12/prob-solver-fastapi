import json
from fastapi import Depends, Request
from langgraph.types import Send
from typing_extensions import TypedDict
from langchain_core.messages import HumanMessage,SystemMessage

from app.vlog_creation.schema import Section, WorkerState, State
from app.vlog_creation.dependencies import get_ai_model
from app.adapter.groq_ai import Groq_AIModelAdapter
from _core.utility import get_planner
from _core.registry import get_ai_model

# Nodes for the graph
class Nodes:

    #def __init__(self, request: Request ,model: Groq_AIModelAdapter = Depends(get_ai_model)):
    def __init__(self, model: Groq_AIModelAdapter):
        # Get the planner and LLM from the registry
        self.llm = model.get_llm()
        self.planner = get_planner(model)

    def orchestrator(self,state: State):
        """Orchestrator that generates a plan for the report"""

        # Generate queries
        report_sections = self.planner.invoke(
            [
                SystemMessage(content="Generate a plan for the report."),
                HumanMessage(content=f"Here is the report topic: {state['topic']}"),
            ]
        )

        #print("Report Sections:",report_sections)

        return {"sections": report_sections.sections}

    def llm_call(self,state: WorkerState):
        """Worker writes a section of the report"""
        try:
            print(f"Section name: {state['section'].name}")
            print(f"Section description: {state['section'].description}")
            # Generate section
            section = self.llm.invoke(
                [
                    SystemMessage(
                        content="Write a report section following the provided name and description. Include no preamble for each section. "
                        + "Do not include any reasoning or inner thoughts. Only return the final output in markdown format, starting immediately with the content." 
                        + "Return the output as a JSON object with a single key 'content' containing the section content."
                        + "Note the json should be enclosed with ````json{'content':'###'}``` so that it can be extracted easily from the generated context."
                    ),
                    HumanMessage(
                        content=f"Here is the section name: {state['section'].name} and description: {state['section'].description}"
                    ),
                ]
            )

            # Write the updated section to completed sections
            split = section.content.split("```json")[1]
            json_content = split.split("```")[0].strip()
            json_content = json_content.replace(".", "")  # Ensure valid JSON format
            json_content = json.loads(json_content)  # Parse the JSON content
            #return {"completed_sections": [section.content]}
            print("Genereted content", json_content)
            print("*" * 20 )
            return {"completed_sections": [json_content['content']]}
        except Exception as e:
            print(f"Error in llm_call: {e}, for section: {state['section'].name}")
            print("*" * 20 )
            return {"completed_sections": ['']}
            #raise RuntimeError("Failed to generate section content") from e

        # Befor returning the section we need to format or extract the content from the section

    # Conditional edge function to create llm_call workers that each write a section of the report
    def assign_workers(self,state: State):
        """Assign a worker to each section in the plan"""

        # Kick off section writing in parallel via Send() API
        sends = [Send("llm_call", {"section": s}) for s in state["sections"]]
        #print("list of sends:", sends)
        return sends

    def synthesizer(self, state: State):
        """Synthesize full report from sections"""
        try:
            # List of completed sections
            completed_sections = state["completed_sections"]
            
            # wnat to remove the empty strings from the list completed_sections
            completed_sections = [section for section in completed_sections if section.strip()]
            
            # Format completed section to str to use as context for final sections
            completed_report_sections = "\n\n---\n\n".join(completed_sections)
            

            return {"final_report": completed_report_sections}
        except Exception as e:
            print(f"Error in synthesizer: {e}")
            raise RuntimeError("Failed to synthesize the final report") from e
    
    def build_workflow(self):
        """Build the workflow graph"""

        from langgraph.graph import StateGraph, START, END
        #from IPython.display import Image, display
        self.orchestrator_worker_builder = StateGraph(State)

        # Add the nodes
        self.orchestrator_worker_builder.add_node("orchestrator", self.orchestrator)
        self.orchestrator_worker_builder.add_node("llm_call", self.llm_call)
        self.orchestrator_worker_builder.add_node("synthesizer", self.synthesizer)

        # Add edges to connect nodes
        self.orchestrator_worker_builder.add_edge(START, "orchestrator")
        self.orchestrator_worker_builder.add_conditional_edges(
            "orchestrator", self.assign_workers, ["llm_call"]
        )
        self.orchestrator_worker_builder.add_edge("llm_call", "synthesizer")
        self.orchestrator_worker_builder.add_edge("synthesizer", END)

    def compile_graph(self):
        """Compile the graph and return the workflow"""
        try:
            self.build_workflow()
            self.orchestrator_worker = self.orchestrator_worker_builder.compile()
            print("grapg compilation is successful",type(self.orchestrator_worker))
            return self.orchestrator_worker
        except Exception as e:
            print(f"Error compiling graph: {e}")
            raise RuntimeError("Failed to compile the workflow graph") from e
