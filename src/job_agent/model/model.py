from langchain_ollama import ChatOllama
from job_agent.utils import load_config


def load_model():
    # need to add exception there will be models that need reasoning
    agent_config = load_config()
    model_name = agent_config['model']
    model = ChatOllama(model=model_name, reasoning=False)
    return model