import json
import os
import re
from typing import TypedDict, List, Annotated
from operator import add
from langgraph.graph import StateGraph, END
from security import SecurityGuard
from dotenv import load_dotenv

from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, BaseMessage

# Load Environment
load_dotenv()

# Define State
class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], add]  # Conversational history
    sanitized_input: str
    identified_role: str
    needs: List[dict]
    plan: List[dict]
    logs: Annotated[List[str], add]
    ready_to_finalize: bool

class WorkflowEngine:
    def __init__(self):
        self.guard = SecurityGuard()
        self.llm = ChatOllama(model="llama3.2", temperature=0.7) 
        self.workflow = self._build_graph()

    def _load_policy(self):
        """Loads policy dynamically."""
        try:
            with open("secure_hr_policy.txt", "r") as f:
                return f.read()
        except FileNotFoundError:
            return "Policy file not found."

    def _load_api_registry(self):
        """Loads API registry dynamically (hot-reload)."""
        try:
            with open("api_registry.json", "r") as f:
                return json.load(f)
        except FileNotFoundError:
            return {"apis": []}

    def _find_api(self, keyword, registry):
        """Helper to find API."""
        for api in registry["apis"]:
            if keyword.lower() in api["name"].lower() or keyword.lower() in api["description"].lower():
                return api
        return None

    # --- Nodes ---

    def guard_node(self, state: AgentState):
        """
        Node 1: Security Guardrail - Redact PII in latest message.
        """
        messages = state["messages"]
        last_message = messages[-1]
        
        if isinstance(last_message, HumanMessage):
            sanitized = self.guard.anonymize_input(last_message.content)
            # Replace the original with sanitized for internal processing? 
            # Or just keep sanitized string separate.
            return {"sanitized_input": sanitized}
        
        return {}

    def assistant_node(self, state: AgentState):
        """
        Node 2: Conversational Assistant.
        Reads history, decides if info is missing.
        """
        messages = state["messages"]
        policy = self._load_policy()
        
        system_prompt = f"""You are an HR Onboarding Assistant.
        Your goal is to gather necessary details from the user to create an onboarding workflow.
        
        HR POLICY:
        {policy}
        
        INSTRUCTIONS:
        1. Analyze the user's request.
        2. Check if you have enough information to determine the Employee Role and specific needs (Relocation, Training, etc).
        3. If information is missing (e.g., Seniority for relocation tier, Gender for training type for compliance), ASK clarifying questions.
        4. If you have all details, say "CONFIRMED".
        5. Do not hallucinate PII.
        """
        
        # We need to prepend system prompt to messages
        prompt_messages = [SystemMessage(content=system_prompt)] + messages
        
        response = self.llm.invoke(prompt_messages)
        content = response.content
        
        ready = "CONFIRMED" in content
        
        return {
            "messages": [response], 
            "ready_to_finalize": ready,
            "logs": ["🗣️ Assistant Replied"]
        }

    def planner_extractor_node(self, state: AgentState):
        """
        Node 3: Plan Extraction (runs only when confirmed).
        """
        # Extract structured data from conversation history
        messages = state["messages"]
        policy = self._load_policy()
        
        extraction_prompt = f"""Based on the conversation history below and the HR Policy, extract the final Onboarding Plan.
        
        HR POLICY:
        {policy}
        
        Return STRICT JSON format:
        {{
            "identified_role": "...",
            "needs": [ {{"type": "...", "detail": "..."}} ]
        }}
        """
        
        # ... Implementation of structured extraction ...
        # Simplified for Hackathon:
        # We can reuse the previous Planner logic but feed it the entire conversation history instead of just one input.
        # For brevity, let's assume we use the last sanitized input context or summarize.
        
        # Mock logic or LLM call here
        return {"identified_role": "Senior Engineer", "needs": [{"type": "Relocation", "detail": "Tier-2"}]}

    def executor_node(self, state: AgentState):
        """
        Node 4: Execution (same as before).
        """
        # ... Identical logic ...
        return {"plan": [], "logs": []}

    def _build_graph(self):
        workflow = StateGraph(AgentState)

        workflow.add_node("guard", self.guard_node)
        workflow.add_node("assistant", self.assistant_node)
        # workflow.add_node("planner", self.planner_extractor_node)
        # workflow.add_node("executor", self.executor_node)

        workflow.set_entry_point("guard")
        workflow.add_edge("guard", "assistant")
        
        # Conditional Edge
        def check_ready(state):
            if state.get("ready_to_finalize"):
                return "END" # Or 'planner' -> 'executor'
            return END
            
        workflow.add_edge("assistant", END) # For now, let's just chat.

        return workflow.compile()

    def process_request(self, user_input: str):
        """
        Run the LangGraph workflow.
        """
        # Get current messages from state
        # In a real app we'd pass the full history, but here we just pass the new input
        # and rely on the state graph to potentially use history if we persisted it better.
        # For this simple demo, we construct the input message.
        
        current_messages = [HumanMessage(content=user_input)]
        
        initial_state = {
            "messages": current_messages,
            "sanitized_input": "",
            "identified_role": "",
            "needs": [],
            "plan": [],
            "logs": [],
            "ready_to_finalize": False
        }
        
        # Invoke the graph
        final_state = self.workflow.invoke(initial_state)
        
        # Return the last assistant message content
        last_message = final_state["messages"][-1]
        return last_message.content
