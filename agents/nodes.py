from langchain_core.messages import HumanMessage, ToolMessage, AIMessage
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers.openai_tools import JsonOutputKeyToolsParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from agents.tools import verify_document, provision_it_resources, create_hr_record
import json
import os

# --- Custom Agent Implementation ---

class SimpleAgentExecutor:
    """
    A simple agent loop that replaces LangChain's AgentExecutor.
    It calls the model, executes tools, and repeats until no tool calls are made.
    """
    def __init__(self, llm, tools, system_prompt):
        if llm:
            self.llm = llm.bind_tools(tools)
        else:
            self.llm = None
        self.tools = {t.name: t for t in tools}
        self.system_prompt = system_prompt

    def invoke(self, state):
        if not self.llm:
            return {"output": "Error: LLM not initialized (missing API Key)."}
            
        # Prepare messages: System prompt + conversation history
        history = state.get("messages", [])
        
        current_messages = [HumanMessage(content=self.system_prompt)] + list(history)
        
        # Execution loop
        steps = 0
        final_output = ""
        
        while steps < 5:
            response = self.llm.invoke(current_messages)
            current_messages.append(response)
            
            if not response.tool_calls:
                final_output = response.content
                break
            
            # Execute tools
            for tool_call in response.tool_calls:
                tool_name = tool_call["name"]
                if tool_name in self.tools:
                    tool_result = self.tools[tool_name].invoke(tool_call["args"])
                    current_messages.append(ToolMessage(
                        tool_call_id=tool_call["id"],
                        content=str(tool_result),
                        name=tool_name
                    ))
                else:
                    current_messages.append(ToolMessage(
                        tool_call_id=tool_call["id"],
                        content=f"Error: Tool {tool_name} not found.",
                        name=tool_name
                    ))
            steps += 1
            
        return {"output": final_output}

def create_agent(llm, tools, system_prompt):
    return SimpleAgentExecutor(llm, tools, system_prompt)

def agent_node(state, agent, name):
    result = agent.invoke(state)
    return {"messages": [HumanMessage(content=result["output"], name=name)]}

# --- Supervisor ---

def create_supervisor_chain(llm, members):
    system_prompt = (
        "You are a supervisor tasked with managing a conversation between the"
        " following workers: {members}. Given the following user request,"
        " respond with the next worker to act. Each worker will perform a"
        " task and respond with their results and status. When finished,"
        " respond with FINISH."
    )
    options = ["FINISH"] + members
    
    # Define route tool
    route_tool = {
        "name": "route",
        "description": "Select the next role.",
        "parameters": {
            "type": "object",
            "properties": {
                "next": {
                    "type": "string",
                    "enum": options,
                }
            },
            "required": ["next"],
        },
    }

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        MessagesPlaceholder(variable_name="messages"),
        (
            "system",
            "Given the conversation above, who should act next?"
            " Or should we FINISH? Select one of: {options}",
        ),
    ]).partial(options=str(options), members=", ".join(members))
    
    if llm:
        chain = (
            prompt
            | llm.bind_tools(tools=[route_tool], tool_choice="route")
            | JsonOutputKeyToolsParser(key_name="route", first_tool_only=True)
        )
    else:
        # Dummy chain if LLM failed to init
        chain = prompt | (lambda x: {"next": "FINISH"}) # Fallback
        
    return chain

# --- Agent Instances ---

# Robust initialization
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    # Set dummy to pass validation, invoke will fail but server starts
    os.environ["OPENAI_API_KEY"] = "dummy"

try:
    llm = ChatOpenAI(model="gpt-4o")
except Exception as e:
    print(f"WARNING: Could not initialize ChatOpenAI: {e}")
    llm = None

# 1. Document Verifier
doc_agent = create_agent(
    llm, 
    [verify_document], 
    "You are a Document Verification Specialist. Your job is to verify uploaded documents. Use the 'verify_document' tool."
)

# 2. IT Provisioner
it_agent = create_agent(
    llm, 
    [provision_it_resources], 
    "You are an IT Provisioning Specialist. Your job is to create accounts for new employees. Use the 'provision_it_resources' tool."
)

# 3. HR Specialist
hr_agent = create_agent(
    llm, 
    [create_hr_record], 
    "You are an HR Specialist. Your job is to update records and send welcome emails after everything else is done. Use the 'create_hr_record' tool."
)
