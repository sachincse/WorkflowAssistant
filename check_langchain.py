import langchain
import langchain.agents
print(f"LangChain Version: {langchain.__version__}")
try:
    from langchain.agents import create_tool_calling_agent
    print("create_tool_calling_agent found")
except ImportError:
    print("create_tool_calling_agent NOT found")
    # limit output length
    print("Available agents:", dir(langchain.agents)[:20])
