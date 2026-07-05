from langchain_core.messages import (SystemMessage, 
                                     HumanMessage)
from langchain_ollama import ChatOllama
from prompts import SYSTEM_PROMPT #type: ignore



def main():
    # set up LLM & list of messages
    messages = [
        SystemMessage(content=SYSTEM_PROMPT)
    ]
    
    llm = ChatOllama(model="llama3.1", reasoning=True)
    
    user_input = ""
    # make call, if tool needed use the tool func else give output to user
    while user_input != "exit":
        messages.extend([HumanMessage(content=user_input)])
        llm_output = llm.stream(messages)
        
        for i in llm_output:
            print(i)
        
        new_user_input = input('What to ask next')
        user_input = new_user_input


if __name__ == "__main__":
    print("Starting")
    main()