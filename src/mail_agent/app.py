from typing import Any, List

from mail_agent.agent import build_graph
from mail_agent.model import load_model
from mail_agent.mcp import connect_to_mcp
from mail_agent.utils import load_config

from langchain.messages import HumanMessage, SystemMessage, AnyMessage, ToolMessage
from langchain_core.runnables import RunnableConfig

from collections.abc import AsyncIterator


class MailAgent():
    def __init__(self) -> None:
        self.graph = build_graph()
        self.llm = load_model()
        self.mcp_client = connect_to_mcp()
        self.tools_registory: dict = dict()
        self.system_prompt = None

        # initialy the tools will be empty, 
        # setting llm and tools none at initialization
        #  since we may need add or remove tools at runtime
        #  without initializing the agent again
        self.config = RunnableConfig(configurable={"thread_id": '1', "llm": None, "tools": None})
        
    async def intialize(self) -> None:
        # initialize cores
        # Create a tool registory for easy access to tools
        self.available_mcp_tools = await self.mcp_client.get_tools()
        if self.available_mcp_tools:
            self.tools_registory = {tool.name: tool for tool in self.available_mcp_tools}

        # Use an activated tools list which user 
        # can activate only a set of tools or no tools
        self.system_prompt = await self.mcp_client.get_prompt('gmail', 'system_prompt') # mcp_server, prompt_name

    
    def build_message(self, user_input: str) -> List[AnyMessage]:
        """get's message list from graph, build message if graph starting""" 

        # if there is messages in graph state values we append new user message
        # else we create new messages for fresh start
        messages = self.graph.get_state(self.config).values.get('messages', None) #type: ignore
        if messages:
            # truncate to last 4 messages
            messages = messages[-4:]
            messages.append(HumanMessage(content=user_input))
            return messages
        
        else:
            messages = [
                SystemMessage(content=str(self.system_prompt) if self.system_prompt else ""),
                HumanMessage(content=user_input)
            ]
        
            return messages
        
    
    def load_runnable_config(self):
        # Update the runnable config for each input
        # to check if there is any added or removed tools
        self.agent_config = load_config()
        # set normal llm first
        # use this if there is no tools is using
        llm = self.llm 
        if self.agent_config['enabled_tools']:
            tools = [self.tools_registory[tool_name] for tool_name in self.agent_config['enabled_tools']]
            llm = self.llm.bind_tools(tools)
        config = RunnableConfig(configurable={"thread_id": '1', "llm": llm, "tools": self.tools_registory})
        return config
        

    async def stream(self, user_input: str) -> AsyncIterator[dict[str, Any]]:
        messages = self.build_message(user_input=user_input)
        input_state = {"messages": messages}
        config = self.load_runnable_config()

        # async for type, msg in self.graph.astream(input_state, config=config, stream_mode='messages'): #type: ignore
        #     # Skip tool message in ui
        #     if isinstance(msg, ToolMessage):
        #         continue
        #     yield msg.content #type: ignore

        async for type, msg in self.graph.astream(input_state, config=config, stream_mode=['messages', 'custom']): #type: ignore
            # Skip tool message in ui
            if isinstance(msg[0], ToolMessage): # ( type, (BaseMessage, langgraph metadata))
                continue

            if type == "custom":
                yield {"type":"status", "data": msg}
            else:
                yield {"type":"token", "data": msg[0].content} #type: ignore