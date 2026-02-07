import json
import time
from typing import TypedDict, List, Annotated
from operator import add
from langgraph.graph import StateGraph, END
from security import SecurityGuard
from dotenv import load_dotenv

import os
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, BaseMessage

# Import Real Email Service
from email_service import send_real_email

# Import Policy Manager
from policy_manager import PolicyManager

load_dotenv()

class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], add]
    sanitized_input: str
    identified_role: str
    needs: List[dict]
    plan: List[dict]
    logs: Annotated[List[str], add]
    ready_to_finalize: bool

class WorkflowEngine:
    def __init__(self):
        self.guard = SecurityGuard()
        # Use OpenAI GPT-4
        self.llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)
        self.policy_manager = PolicyManager()
        self.workflow = self._build_graph()

    def _load_policy(self):
        """Load all policy documents"""
        policies = self.policy_manager.get_all_policies()
        # Combine all policies into one string
        combined = "\n\n=== COMBINED POLICIES ===\n\n"
        for name, content in policies.items():
            combined += f"\n--- {name.upper().replace('_', ' ')} ---\n{content}\n"
        return combined

    def load_api_registry(self):
        try:
            with open("api_registry.json", "r") as f:
                return json.load(f)
        except:
            return {"apis": []}

    # --- Nodes ---
    def guard_node(self, state: AgentState):
        return {}

    def assistant_node(self, state: AgentState):
        """
        Real conversational node. 
        Queries GPT-4 to respond to the user based on history and ALL policies.
        """
        messages = state["messages"]
        policy = self._load_policy()
        
        # Get dynamic mandatory fields from policies
        mandatory_fields = self.policy_manager.extract_mandatory_fields()
        fields_list = "\n".join([f"{i+1}. **{f['display_name']}**: {f['reason']}" 
                                 for i, f in enumerate(mandatory_fields)])
        
        system_prompt = f"""You are an HR Onboarding Assistant.
        Your goal is to gather specific details to onboard an employee.
        
        ALL POLICIES (CONFIDENTIAL):
        {policy}
        
        REQUIRED INFORMATION (from policies):
        {fields_list}
        
        INSTRUCTIONS:
        - REVIEW the conversation history. Identify which of the required fields are missing.
        - Create a checklist in your mind. If ANY field is missing, ASK for it specifically.
        - DO NOT finalize the workflow until ALL required fields are present.
        - If the user provides everything, confirm with a summary listing all collected information.
        - ONLY when the user says "Yes" or "Confirm" AFTER the summary, reply with "CONFIRMED".
        """
        
        response = self.llm.invoke([SystemMessage(content=system_prompt)] + messages)
        content = response.content
        
        # Stricter finalization check
        ready = "CONFIRMED" in content and len(messages) > 2 # Ensure at least some convo happened
        
        return {
            "messages": [response],
            "ready_to_finalize": ready
        }

    def planner_extractor_node(self, state: AgentState):
        """
        Extract structured workflow from conversation based on HR Policy.
        """
        messages = state["messages"]
        policy = self._load_policy()
        
        # Use LLM to extract structured data from conversation
        extraction_prompt = f"""Based on the conversation history and HR Policy below, extract the employee details and determine ALL required onboarding actions.

HR POLICY:
{policy}

CONVERSATION HISTORY:
{self._format_messages(messages)}

Extract the following in JSON format:
{{
    "employee_name": "...",
    "role": "...",
    "location": "...",
    "gender": "...",
    "needs": [
        {{"type": "Relocation", "detail": "Tier-X Package", "reason": "Based on role"}},
        {{"type": "Training", "detail": "POSH Training", "reason": "Mandatory for all"}},
        {{"type": "Training", "detail": "Gender Sensitization/Safety Labs", "reason": "Based on gender"}},
        {{"type": "Communication", "detail": "Welcome Email"}},
        {{"type": "ID_Card", "detail": "Generate Employee ID Card"}},
        {{"type": "System_Access", "detail": "Create HR System Account"}}
    ]
}}

IMPORTANT: 
- Include ALL applicable items from the policy
- Determine relocation tier based on role (Senior Engineer=Tier-2, Manager=Tier-1, Junior=Tier-3)
- Include gender-specific training
- Always include POSH training, Welcome Email, ID Card, and System Access
"""
        
        try:
            response = self.llm.invoke([HumanMessage(content=extraction_prompt)])
            import json
            # Parse JSON from response
            content = response.content
            # Extract JSON from markdown code blocks if present
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            data = json.loads(content)
            
            return {
                "identified_role": data.get("role", "Employee"),
                "needs": data.get("needs", [])
            }
        except Exception as e:
            # Fallback to basic needs
            return {
                "identified_role": "Employee",
                "needs": [
                    {"type": "Communication", "detail": "Welcome Email"},
                    {"type": "Training", "detail": "POSH Training"},
                ]
            }
    
    def _format_messages(self, messages):
        """Helper to format messages for LLM"""
        formatted = []
        for msg in messages:
            role = "User" if isinstance(msg, HumanMessage) else "Assistant"
            formatted.append(f"{role}: {msg.content}")
        return "\n".join(formatted)

    def executor_node(self, state: AgentState):
        """Executes the complete workflow - ALL actions from policy"""
        needs = state["needs"]
        plan = []
        logs = []
        registry = self.load_api_registry()
        
        target_email = os.getenv("TARGET_TEST_EMAIL", "sachincs95@gmail.com")
        
        logs.append(f"🚀 Executing {len(needs)} workflow actions...")
        
        for need in needs:
            action_type = need.get("type", "Unknown")
            detail = need.get("detail", "")
            
            # 1. RELOCATION / TRAVEL
            if action_type == "Relocation":
                api = self._find_api("Travel", registry)
                if api and api["status"] == "active":
                    plan.append({
                        "step": f"Book Travel: {detail}",
                        "tool": api["name"],
                        "status": "✅ Automated",
                        "api_call": f"POST /travel/book (tier={detail})"
                    })
                    logs.append(f"✈️ Travel booking initiated via {api['name']}")
                else:
                    plan.append({
                        "step": f"Book Travel: {detail}",
                        "tool": "Manual (Admin Portal)",
                        "status": "⚠️ Manual Fallback",
                        "note": "Travel API in maintenance"
                    })
                    logs.append(f"⚠️ Travel API unavailable - manual booking required")
            
            # 2. TRAINING
            elif action_type == "Training":
                api = self._find_api("LMS", registry)
                if api and api["status"] == "active":
                    plan.append({
                        "step": f"Assign Training: {detail}",
                        "tool": api["name"],
                        "status": "✅ Automated",
                        "api_call": f"POST /lms/assign (course={detail})"
                    })
                    logs.append(f"📚 Training assigned via {api['name']}")
                else:
                    plan.append({
                        "step": f"Assign Training: {detail}",
                        "tool": "Manual Assignment",
                        "status": "⚠️ Manual Fallback"
                    })
            
            # 3. COMMUNICATION / EMAIL
            elif action_type == "Communication":
                api = self._find_api("SendGrid", registry)
                if api and api["status"] == "active":
                    # Actually send the email
                    email_status = send_real_email(
                        to_email=target_email,
                        subject="Welcome to Deriv!",
                        body=f"Dear Employee,\n\nWelcome to Deriv! Your onboarding process has been initiated.\n\nPlease complete the following:\n- POSH Training\n- Gender Sensitization Workshop\n- ID Card Collection\n\nBest regards,\nHR Team"
                    )
                    
                    if "Application-specific password required" in email_status:
                        email_status = "❌ Failed: Invalid Gmail Password. Please generate an 'App Password' in Google Security settings."
                    
                    plan.append({
                        "step": "Send Welcome Email",
                        "tool": "Gmail SMTP",
                        "status": email_status,
                        "api_call": f"SMTP send to {target_email}"
                    })
                    logs.append(f"📧 {email_status}")
                else:
                    plan.append({
                        "step": "Send Welcome Email",
                        "tool": "Manual Email",
                        "status": "⚠️ Manual Fallback"
                    })
            
            # 4. ID CARD GENERATION
            elif action_type == "ID_Card":
                api = self._find_api("HR", registry)  # Changed from "HR_Core" to "HR"
                if api and api["status"] == "active":
                    plan.append({
                        "step": "Generate Employee ID Card",
                        "tool": api["name"],
                        "status": "✅ Automated",
                        "api_call": "POST /hr/id-card/generate"
                    })
                    logs.append(f"🪪 ID Card generation initiated via {api['name']}")
                else:
                    plan.append({
                        "step": "Generate Employee ID Card",
                        "tool": "Manual Process",
                        "status": "⚠️ Manual Fallback"
                    })
            
            # 5. SYSTEM ACCESS
            elif action_type == "System_Access":
                api = self._find_api("HR", registry)  # Changed from "HR_Core" to "HR"
                if api and api["status"] == "active":
                    plan.append({
                        "step": "Create HR System Account",
                        "tool": api["name"],
                        "status": "✅ Automated",
                        "api_call": "POST /hr/accounts/create"
                    })
                    logs.append(f"👤 System account created via {api['name']}")
                else:
                    plan.append({
                        "step": "Create HR System Account",
                        "tool": "Manual Setup",
                        "status": "⚠️ Manual Fallback"
                    })
            
            # 6. INSURANCE / HEALTHCARE
            elif action_type == "Insurance" or action_type == "Healthcare":
                api = self._find_api("Insurance", registry)
                if api and api["status"] == "active":
                    plan.append({
                        "step": f"Enroll in Health Insurance: {detail}",
                        "tool": api["name"],
                        "status": "✅ Automated",
                        "api_call": "POST /insurance/enroll"
                    })
                    logs.append(f"🏥 Health insurance enrollment initiated via {api['name']}")
                else:
                    plan.append({
                        "step": f"Enroll in Health Insurance: {detail}",
                        "tool": "Manual Enrollment",
                        "status": "⚠️ Manual Fallback"
                    })
            
            # 7. FALLBACK for unknown types
            else:
                plan.append({
                    "step": f"Process: {detail}",
                    "tool": "Manual Review",
                    "status": "⚠️ Manual Fallback"
                })
        
        logs.append(f"✅ Workflow execution complete: {len(plan)} actions processed")
        return {"plan": plan, "logs": logs}
    
    def _find_api(self, keyword, registry):
        """Helper to find API in registry"""
        for api in registry.get("apis", []):
            if keyword.lower() in api["name"].lower().replace("_", " "):
                return api
        return None
        
    def _build_graph(self):
        workflow = StateGraph(AgentState)
        workflow.add_node("guard", self.guard_node)
        workflow.add_node("assistant", self.assistant_node)
        workflow.add_node("planner", self.planner_extractor_node)
        workflow.add_node("executor", self.executor_node)

        workflow.set_entry_point("guard")
        workflow.add_edge("guard", "assistant")
        
        def check_ready(state):
            if state.get("ready_to_finalize"):
                return "planner"
            return END
        
        workflow.add_conditional_edges("assistant", check_ready)
        workflow.add_edge("planner", "executor")
        workflow.add_edge("executor", END)
        
        return workflow.compile()

    def process_request(self, user_input: str, history: List[dict] = None):
        """
        Run the LangGraph workflow with conversation context.
        """
        # Convert history (list of dicts) to LangChain Messages
        # This is CRITICAL for the LLM to remember context.
        messages = []
        if history:
            for msg in history:
                if msg["role"] == "user":
                    messages.append(HumanMessage(content=msg["content"]))
                elif msg["role"] == "assistant":
                    messages.append(AIMessage(content=msg["content"]))
        
        # Add current input
        messages.append(HumanMessage(content=user_input))
        
        initial_state = {
            "messages": messages, # PASS FULL HISTORY
            "sanitized_input": "",
            "identified_role": "",
            "needs": [],
            "plan": [],
            "logs": [],
            "ready_to_finalize": False
        }
        
        final_state = self.workflow.invoke(initial_state)
        
        if final_state.get("ready_to_finalize"):
            plan = final_state.get("plan", [])
            
            # Create detailed workflow summary
            workflow_summary = "✅ **Workflow Finalized & Executed!**\n\n"
            workflow_summary += f"**Total Actions: {len(plan)}**\n\n"
            
            # Group by status
            automated = [p for p in plan if "✅" in p.get("status", "")]
            manual = [p for p in plan if "⚠️" in p.get("status", "")]
            failed = [p for p in plan if "❌" in p.get("status", "")]
            
            if automated:
                workflow_summary += "### ✅ Automated Actions\n"
                for step in automated:
                    workflow_summary += f"- **{step['step']}**\n"
                    workflow_summary += f"  - Tool: {step['tool']}\n"
                    workflow_summary += f"  - Status: {step['status']}\n"
                    if 'api_call' in step:
                        workflow_summary += f"  - API: `{step['api_call']}`\n"
                    workflow_summary += "\n"
            
            if manual:
                workflow_summary += "### ⚠️ Manual Actions Required\n"
                for step in manual:
                    workflow_summary += f"- **{step['step']}**\n"
                    workflow_summary += f"  - Tool: {step['tool']}\n"
                    if 'note' in step:
                        workflow_summary += f"  - Note: {step['note']}\n"
                    workflow_summary += "\n"
            
            if failed:
                workflow_summary += "### ❌ Failed Actions\n"
                for step in failed:
                    workflow_summary += f"- **{step['step']}**: {step['status']}\n\n"
            
            return workflow_summary
            
        return final_state["messages"][-1].content
