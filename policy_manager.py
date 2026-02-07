"""
Policy Manager - Handles dynamic policy loading and field extraction
"""
import os
import re
from typing import List, Dict
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from dotenv import load_dotenv

load_dotenv()

class PolicyManager:
    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
        self.policy_dir = os.path.dirname(os.path.abspath(__file__))
        
    def get_all_policies(self) -> Dict[str, str]:
        """Load all policy documents"""
        policies = {}
        
        # Load HR Policy
        hr_policy_path = os.path.join(self.policy_dir, "secure_hr_policy.txt")
        if os.path.exists(hr_policy_path):
            with open(hr_policy_path, 'r') as f:
                policies['hr_policy'] = f.read()
        
        # Load Healthcare Policy
        healthcare_path = os.path.join(self.policy_dir, "healthcare_policy.txt")
        if os.path.exists(healthcare_path):
            with open(healthcare_path, 'r') as f:
                policies['healthcare_policy'] = f.read()
        
        return policies
    
    def extract_mandatory_fields(self) -> List[str]:
        """
        Use LLM to extract all mandatory fields from policies
        """
        policies = self.get_all_policies()
        combined_policy = "\n\n".join(policies.values())
        
        prompt = f"""Analyze the following HR and Healthcare policies and extract ALL mandatory employee information fields.

POLICIES:
{combined_policy}

Return a JSON list of mandatory fields. For each field, include:
- field_name: The name of the field (e.g., "blood_group", "phone_number")
- display_name: Human-readable name (e.g., "Blood Group", "Phone Number")
- reason: Why it's mandatory
- source: Which policy requires it

Example format:
[
    {{"field_name": "name", "display_name": "Employee Name", "reason": "Basic identification", "source": "HR Policy"}},
    {{"field_name": "blood_group", "display_name": "Blood Group", "reason": "Emergency medical records", "source": "HR Policy"}}
]

Return ONLY the JSON array, no other text.
"""
        
        try:
            response = self.llm.invoke([HumanMessage(content=prompt)])
            content = response.content
            
            # Extract JSON from markdown if present
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            import json
            fields = json.loads(content)
            return fields
        except Exception as e:
            # Fallback to basic fields
            return [
                {"field_name": "name", "display_name": "Employee Name", "reason": "Basic identification", "source": "HR Policy"},
                {"field_name": "role", "display_name": "Job Role", "reason": "Access determination", "source": "HR Policy"},
                {"field_name": "location", "display_name": "Location", "reason": "Relocation eligibility", "source": "HR Policy"},
                {"field_name": "gender", "display_name": "Gender", "reason": "Training assignment", "source": "HR Policy"}
            ]
    
    def extract_required_actions(self, policies: Dict[str, str]) -> List[Dict]:
        """
        Extract all required onboarding actions from policies
        """
        combined_policy = "\n\n".join(policies.values())
        
        prompt = f"""Analyze the following policies and extract ALL mandatory onboarding actions.

POLICIES:
{combined_policy}

Return a JSON list of actions. For each action, include:
- type: Action type (e.g., "Insurance", "Training", "Communication")
- detail: Description of the action
- source: Which policy requires it
- mandatory: true/false

Example:
[
    {{"type": "Insurance", "detail": "Enroll in Health Insurance", "source": "Healthcare Policy", "mandatory": true}},
    {{"type": "Training", "detail": "POSH Training", "source": "HR Policy", "mandatory": true}}
]

Return ONLY the JSON array.
"""
        
        try:
            response = self.llm.invoke([HumanMessage(content=prompt)])
            content = response.content
            
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            import json
            actions = json.loads(content)
            return actions
        except:
            return []
    
    def save_policy(self, policy_name: str, content: str) -> bool:
        """Save a new or updated policy document"""
        try:
            filename = f"{policy_name.lower().replace(' ', '_')}_policy.txt"
            filepath = os.path.join(self.policy_dir, filename)
            
            with open(filepath, 'w') as f:
                f.write(content)
            
            return True
        except Exception as e:
            print(f"Error saving policy: {e}")
            return False
    
    def get_policy_summary(self) -> str:
        """Get a summary of all active policies"""
        policies = self.get_all_policies()
        
        summary = "📋 **Active Policies**\n\n"
        for name, content in policies.items():
            lines = content.split('\n')
            first_line = lines[0] if lines else "No description"
            summary += f"- **{name.replace('_', ' ').title()}**: {first_line}\n"
        
        return summary
