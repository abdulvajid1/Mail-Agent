from job_agent.agent import build_graph
from job_agent.model import load_model
from job_agent.prompts import SYSTEM_PROMPT
from job_agent.tools import send_mail
from langchain.messages import HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig


def main():
    app = build_graph()
    llm = load_model()
    tools = [send_mail]

    if tools:
        llm = llm.bind_tools(tools)

    tool_registory = {tool.name: tool for tool in tools}

    user_input = "send a mail to my mother@gmail.com saying i am good from me@gmail.com"    
    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=user_input)
    ]

    input_state = {"messages": messages}
    config = RunnableConfig(configurable={'thread_id': "1", "llm": llm, "tools": tool_registory})

    for msg, _ in app.stream(input_state, config, stream_mode='messages'): # type: ignore
        print(msg.content, end='', flush=True) # type: ignore

    state = app.get_state(config)
    messages = state.values['messages']
    for msg in messages:
        msg.pretty_print()

    
if __name__ == "__main__":
    main()


        # user_input = input("User: ")
