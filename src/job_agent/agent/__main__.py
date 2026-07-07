from langchain_core.messages import (SystemMessage, 
                                     HumanMessage)
from langchain_core.runnables import RunnableConfig
from job_agent.prompts.system_prompt import SYSTEM_PROMPT 
from job_agent.model import load_model
from langgraph.pregel import Pregel

from job_agent.agent import build_graph

def test_graph(app: Pregel, llm):
    user_input = input("Test the graph execution: ")
    config = RunnableConfig(configurable={"thread_id": "1", "llm": llm})
    state = {"messages": [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=user_input)
    ]}
    
    for msg_chunk, _ in app.stream(state, config=config, stream_mode='messages'): # _ for metadata, won't need now
        print(msg_chunk.content, end='', flush=True) # type: ignore

if __name__ == "__main__":
    print("Starting the AGENT....")
    llm = load_model()
    graph = build_graph()
    test_graph(graph, llm)