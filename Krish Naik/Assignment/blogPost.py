from langgraph.graph import StateGraph, START, END
from typing_extensions import TypedDict
from pydantic import BaseModel, Field
from typing import Annotated, List
import operator
from langgraph.constants import Send
from IPython.display import Image, display
from langchain_core.messages import HumanMessage, SystemMessage
import os
from langchain_groq import ChatGroq
from dotenv import load_dotenv
load_dotenv()

os.environ["GROQ_API_KEY"]=os.getenv("GROQ_API_KEY")
os.environ["LANGSMITH_API_KEY"]=os.getenv("LANGCHAIN_API_KEY")
llm=ChatGroq(model="qwen-2.5-32b")

class Section(BaseModel):
    name: str = Field(
        description="Name for this section of the blog",
    )
    description: str = Field(
        description="Brief overview of the main topics and concepts to be covered in this section.",
    )
class Sections(BaseModel):
    sections: List[Section] = Field(
        description="Sections of the report.",
    )

# Augment the LLM with schema for structured output
planner = llm.with_structured_output(Sections)

# Graph state
class InputState(TypedDict):
    topic: str  # Report topic
    
# Delegate state
class DelegateState(TypedDict):
    sections: list[Section]  # List of report sections

# Worker state
class WorkerState(TypedDict):
    section: Section

# Synthesizer state
class SynthesizerState(TypedDict):
    completed_sections: Annotated[
        list, operator.add
    ]  # All workers write to this key in parallel
    final_report: str  # Final report


# Nodes
def orchestrator(state: InputState):
    """Orchestrator that generates a plan for the report"""

    # Generate queries
    result = planner.invoke(
        [
            SystemMessage(content="Generate a plan for the blog post which includes indroduction,  sections followed by overall conclusion."),
            HumanMessage(content=f"Here is the report topic: {state['topic']}"),
        ]
    )
    return {"sections": result.sections}

def llm_generate_sub_sections(state: WorkerState):
    """Worker writes a section of the report"""

    # Generate section
    section = llm.invoke(
        [
            SystemMessage(
                content="Write a blog section following the provided name and description. Include no preamble for each section. Use markdown formatting."
            ),
            HumanMessage(
                content=f"Here is the section name: {state['section'].name} and description: {state['section'].description}"
            ),
        ]
    )

    # Write the updated section to completed sections
    return {"completed_sections": [section.content]}

def synthesizer(state: SynthesizerState):
    """Synthesize full report from sections"""

    # List of completed sections
    completed_sections = state["completed_sections"]

    # Format completed section to str to use as context for final sections
    completed_report_sections = "\n\n---\n\n".join(completed_sections)

    return {"final_report": completed_report_sections}

# Conditional edge function to create llm_call workers that each write a section of the report
def assign_workers(state: DelegateState):
    """Assign a worker to each section in the plan"""

    # Kick off section writing in parallel via Send() API
    return [Send("llm_generate_sub_sections", {"section": s}) for s in state["sections"]]
def createTheWorkFlow():
    # Build workflow
    orchestrator_worker_builder = StateGraph(InputState)

    # Add the nodes
    orchestrator_worker_builder.add_node("orchestrator", orchestrator)
    orchestrator_worker_builder.add_node("llm_generate_sub_sections", llm_generate_sub_sections)
    orchestrator_worker_builder.add_node("synthesizer", synthesizer)

    # Add edges to connect nodes
    orchestrator_worker_builder.add_edge(START, "orchestrator")
    orchestrator_worker_builder.add_conditional_edges(
        "orchestrator", assign_workers, ["llm_generate_sub_sections"]
    )
    orchestrator_worker_builder.add_edge("llm_generate_sub_sections", "synthesizer")
    orchestrator_worker_builder.add_edge("synthesizer", END)

    agent = orchestrator_worker_builder.compile()
    return agent

agent=createTheWorkFlow()
