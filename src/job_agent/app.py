from typing import Any, List

from job_agent.agent import build_graph
from job_agent.model import load_model
from job_agent.mcp import connect_to_mcp

from langchain.messages import HumanMessage, SystemMessage, AnyMessage
from langchain_core.runnables import RunnableConfig


class MailAgent():
    async def __init__(self) -> None:
        # initialize cores
        self.graph = build_graph()
        self.llm = load_model()
        self.mcp_client = connect_to_mcp()
        self.all_available_tools = await self.mcp_client.get_tools()
        if self.tools_registory:
            self.tools_registory = {tool.name: tool for tool in self.tools_registory}

        # Use an activated tools list which user 
        # can activate only a set of tools or no tools
        self.activated_tools = []
        self.system_prompt = await self.mcp_client.get_prompt('gmail', 'system_prompt')

        # initialy the tools will be empty
        self.graph_config = RunnableConfig(configurable={"thread": 'dummy', "llm": self.llm, "tools": self.activated_tools})

    
    def build_message(self, user_input: str, messages: List[AnyMessage]) -> List[AnyMessage]:
        """get's message list from graph, build message if graph starting""" 
        if messages:
            return messages.append(HumanMessage(content=user_input))
        else:
            messages = [
                SystemMessage(content=self.system_prompt),
                HumanMessage(content=user_input)
            ]
        
            return messages
        

    async def __call__(self, user_input: str) -> Any:
        messages = self.graph.get_state(self.graph_config).values['messages']
        messages = self.build_message(user_input=user_input, messages=messages)
        input_state = {"messages": messages} 

        async for msg, _ in self.graph.astream(input_state, config=self.graph_config, stream_mode='messages'):
            pass

    
    def update_tools(self, tools_needed: list):
        self.activated_tools = {tool_name: self.tools_registory[tool_name] for tool_name in tools_needed}
        return "Updated Tools Using"
