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

    tool_registory = {tool.name: tools for tool in tools}
        

    user_input = "can you send mail to my mother, you can generate a body yourself telling i am sorry for what i have done all these days, my id is vajid@gmail.com and my mothers id is mother@gmail.com"
    # user_input = "how are you, this is not for mail, i am just asking you" 
    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=user_input)
    ]

    input_state = {"messages": messages}
    config = RunnableConfig(configurable={'thread_id': "1", "llm": llm, "tools": tool_registory})

    for msg, _ in app.stream(input_state, config, stream_mode='messages'): # type: ignore
        print(msg.content, end='', flush=True) # type: ignore

    
if __name__ == "__main__":
    main()

