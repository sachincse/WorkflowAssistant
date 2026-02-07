import functools
import operator
from typing import Annotated, Sequence, TypedDict, Union

from langchain_core.messages import BaseMessage
from langgraph.graph import END, StateGraph

from agents.nodes import (
    agent_node,
    create_supervisor_chain,
    doc_agent,
    hr_agent,
    it_agent,
    llm,
)

# The state now includes "next" to track the supervisor's decision
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    next: str

members = ["DocumentVerifier", "ITProvisioner", "HRSpecialist"]

supervisor_chain = create_supervisor_chain(llm, members)

workflow = StateGraph(AgentState)

# Note: The supervisor node returns a dictionary {"next": "..."} 
# which updates the "next" key in the state.
workflow.add_node("Supervisor", supervisor_chain)

workflow.add_node("DocumentVerifier", functools.partial(agent_node, agent=doc_agent, name="DocumentVerifier"))
workflow.add_node("ITProvisioner", functools.partial(agent_node, agent=it_agent, name="ITProvisioner"))
workflow.add_node("HRSpecialist", functools.partial(agent_node, agent=hr_agent, name="HRSpecialist"))

for member in members:
    # Workers always report back to the supervisor
    workflow.add_edge(member, "Supervisor")

# The supervisor determines the next step
conditional_map = {k: k for k in members}
conditional_map["FINISH"] = END

workflow.add_conditional_edges(
    "Supervisor", 
    lambda x: x["next"], 
    conditional_map
)

workflow.set_entry_point("Supervisor")

graph = workflow.compile()
