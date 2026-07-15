from job_agent import MailAgent
from job_agent.utils import is_ollama_running
import asyncio
import typer
import ollama

app = typer.Typer()


async def start_agent_cli():
    agent = MailAgent()
    await agent.intialize()

    user_input = input("User: ")

    while user_input != "exit":
        print("Assistant: ", end="", flush=True)

        async for msg in agent.stream(user_input=user_input):
            print(msg, end="", flush=True)

        user_input = input("\nUser: ")


@app.command()
def start():
    """Start an interactive chat session."""
    asyncio.run(start_agent_cli())


@app.command()
def setup():
    """Setup Each components of the MailAgent
    -- Check Ollama
    -- Check Ollama models
    -- Check Mail auth, if not redirect to MailAgent auth gmail"""
    
    #--------Check if ollama is running--------#
    ollama_running = is_ollama_running()
    if not ollama_running:
        print("You should Setup your ollama")
    else:
        print("Ollama is Working Fine") 
    
    #------Check if there is any model inside ollama----#
    ollama_models = ollama.list().get('models', [])
    if ollama_models:
        print(f"✅ Found {len(ollama_models)} installed model(s):\n")
        for model in ollama_models:
            # Display the model name and its size in Gigabytes
            size_gb = model['size'] / (1024 ** 3)
            print(f"• {model['model']} ({size_gb:.2f} GB)")
    else:
        print("You don't have any models in your ollama, So download it")
        return
    
    #------------

    pass

@app.command()
def mail_auth():
    """Check if already autherized, else autherize the gmail"""
    pass

@app.command()
def enable_email():
    """Activate mail tool
    --  Check if gmail autherized
    -- setup tool"""
    pass


    


if __name__ == "__main__":
    app()