from langchain_ollama import ChatOllama
from mail_agent.utils import load_config


def load_model(model_name: None|str = None):
    # need to add exception there will be models that need reasoning
    if not model_name:
        agent_config = load_config()
        model_name = agent_config['model']
    model = ChatOllama(model=model_name, reasoning=False) # type: ignore
    return model