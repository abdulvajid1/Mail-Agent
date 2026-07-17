from job_agent import MailAgent
from job_agent.utils import is_ollama_running
import asyncio
import typer
import ollama
from pathlib import Path
import json

from job_agent.utils import check_user_authentication
from job_agent.utils import authorize_google_mail
from job_agent.utils import load_config, save_config

app = typer.Typer(no_args_is_help=True)

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
    """Setup Each components of the MailAgent"""

    agent_config = load_config()
    
    #--------Check if ollama is running--------#
    ollama_running = is_ollama_running()
    if not ollama_running:
        print("You should Setup your ollama")
        raise typer.Abort()
    else:
        print("Ollama is Working Fine") 
    
    #------Check if there is any model inside ollama----#
    ollama_models = ollama.list().get('models', [])
    if ollama_models:
        print(f"✅ Found {len(ollama_models)} installed model(s):\n")
    else:
        print("You don't have any models in your ollama, So download it")
        raise typer.Abort()
    
    #--------Chooose Ollama Model -----------------------------#
    all_ollama_model_names = [model['model'] for model in ollama_models]
    for model in ollama_models:
        # Display the model name and its size in Gigabytes
        size_gb = model['size'] / (1024 ** 3)
        print(f"• {model['model']} ({size_gb:.2f} GB)")
    
    selected_model = typer.prompt('Choose an ollama model from the list')
    while selected_model not in all_ollama_model_names:
        print("The selected model is not in the list, Choose another one..")
        for model in ollama_models:
            # Display the model name and its size in Gigabytes
            size_gb = model['size'] / (1024 ** 3)
            print(f"• {model['model']} ({size_gb:.2f} GB)")
        
        selected_model = typer.prompt("Choose an ollama model from the list")

    agent_config['model'] = selected_model

    # ------ Check if user want to autherize with google ----------# 
    # check if authentication done else, authenticate
    user_mail_authenticated =  check_user_authentication() # return cred if already authenticated else None
    if user_mail_authenticated:
        agent_config['mail_authorization'] = True
        print("Google Auth is Good")
    else:
        need_to_authorize = typer.confirm("Do you want to authorize with google for enabling gmail tool")
        if need_to_authorize:
            try:
                authorize_google_mail()
            except Exception as e:
                print(f"There is something wrong with authorization {e}")
                raise typer.Abort()
            
            print("Successfully authorized google mail")

    
    # ------------ Do you User need Mailtool enabled --------------
    if not agent_config['enabled_tools']:
        tool_needed = typer.confirm("Do you wanna enable Mail Tool")
        if tool_needed:
            agent_config["enabled_tools"].append('send_mail') # TODO: Later need to add tools with cli, now just hardcode
            print("Tool Enabled Successfully")

    # Write the fresh config to config file
    save_config(agent_config)
    print("Setup Finished")

@app.command()
def mail_auth():
    """Check if already autherized, else autherize the gmail"""
    authorize_google_mail()
    typer.Abort()

@app.command()
def enable_email():
    """Activate mail tool"""

    agent_config = load_config()
    
    if agent_config['enable_tools']:
        print("Tool already Enabled")
        typer.Abort()
    
    agent_config['enable_tool'] = True

    save_config(agent_config)
    
    print("Tool Enabled")
    typer.Abort()



    


if __name__ == "__main__":
    app()