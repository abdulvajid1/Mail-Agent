from typing import Any, List

from job_agent.agent import build_graph
from job_agent.model import load_model
from job_agent.mcp import connect_to_mcp

from langchain.messages import HumanMessage, SystemMessage, AnyMessage
from langchain_core.runnables import RunnableConfig


class MailAgent():
    def __init__(self) -> None:
        self.graph = build_graph()
        self.llm = load_model()
        self.mcp_client = connect_to_mcp()
        self.available_mcp_tools = None
        self.tools_registory = None
        self.activated_tools = None
        self.system_prompt = None
        self.config = None
        
    async def intialize(self):
        # initialize cores
        self.available_mcp_tools = await self.mcp_client.get_tools()
        if self.available_mcp_tools:
            self.tools_registory = {tool.name: tool for tool in self.available_mcp_tools}

        # Use an activated tools list which user 
        # can activate only a set of tools or no tools
        self.activated_tools = []
        self.system_prompt = await self.mcp_client.get_prompt('gmail', 'system_prompt')

        # initialy the tools will be empty
        self.config = RunnableConfig(configurable={"thread_id": '1', "llm": self.llm, "tools": self.activated_tools})

        return self


    
    def build_message(self, user_input: str) -> List[AnyMessage]:
        """get's message list from graph, build message if graph starting""" 

        # if there is messages in graph state values we append new user message
        # else we create new messages for fresh start
        messages = self.graph.get_state(self.config).values.get('messages', None) #type: ignore
        if messages: 
            messages.append(HumanMessage(content=user_input))
            return messages
        else:
            messages = [
                SystemMessage(content=str(self.system_prompt) if self.system_prompt else ""),
                HumanMessage(content=user_input)
            ]
        
            return messages
        

    async def __call__(self, user_input: str) -> Any:

        messages = self.build_message(user_input=user_input)
        input_state = {"messages": messages} 

        async for msg, _ in self.graph.astream(input_state, config=self.config, stream_mode='messages'): #type: ignore
            print(msg.content, end="", flush=True)

    
    def update_tools(self, tools_needed: list):
        if self.tools_registory:
            self.activated_tools = {tool_name: self.tools_registory[tool_name] for tool_name in tools_needed}
        return "Updated Tools Using"
