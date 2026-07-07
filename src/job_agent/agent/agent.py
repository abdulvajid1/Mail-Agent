from langchain_core.messages import (SystemMessage, 
                                     HumanMessage)
from langchain_core.runnables import RunnableConfig
from src.job_agent.prompts.system_prompt import SYSTEM_PROMPT 
from src.job_agent.model import load_model
from src.job_agent.nodes import chat_node
from src.job_agent.states import AgentState

from langgraph.graph import StateGraph
from langgraph.graph import START, END
from langgraph.pregel import Pregel

from langgraph.checkpoint.memory import MemorySaver

def build_graph():

    graph = StateGraph(AgentState)

    graph.add_node("chat_node", chat_node)
    graph.set_entry_point('chat_node')
    graph.set_finish_point('chat_node')

    app = graph.compile(checkpointer=MemorySaver())
    return app

def test_graph(app: Pregel, llm):
    user_input = input("Test the graph execution: ")
    config = RunnableConfig(configurable={"thread_id": "1", "llm": llm})
    state = {"messages": [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=user_input)
    ]}
    
    for msg, _ in app.stream(state, config=config, stream_mode='messages'):
        print(msg.content, end='', flush=True)




if __name__ == "__main__":
    print("Starting the AGENT....")
    llm = load_model()
    graph = build_graph()
    test_graph(graph, llm)