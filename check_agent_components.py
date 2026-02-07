try:
    from langchain.agents.output_parsers.tools import ToolsAgentOutputParser
    print("ToolsAgentOutputParser found")
except ImportError:
    print("ToolsAgentOutputParser NOT found")

try:
    from langchain.agents.format_scratchpad.tools import format_to_tool_messages
    print("format_to_tool_messages found")
except ImportError:
    print("format_to_tool_messages NOT found")
