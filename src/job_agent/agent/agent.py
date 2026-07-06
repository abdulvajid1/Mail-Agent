from langchain_core.messages import (SystemMessage, 
                                     HumanMessage)
from langchain_ollama import ChatOllama
from src.job_agent.prompts.system_prompt import SYSTEM_PROMPT 



def main():
    # set up LLM & list of messages
    messages = [
        SystemMessage(content=SYSTEM_PROMPT)
    ]
    
    llm = ChatOllama(model="llama3.1")
    
    user_input = input("Ask something")
    # make call, if tool needed use the tool func else give output to user
    while user_input != "exit":
        messages.extend([HumanMessage(content=user_input)]) #type: ignore
        for msg in messages:
            msg.pretty_print()
            
        llm_output = llm.stream(messages)
        
        for i in llm_output:
            print(i.content, end="", flush=True)
        
        new_user_input = input('What to ask next')
        user_input = new_user_input


if __name__ == "__main__":
    print("Starting the AGENT....")
    main()