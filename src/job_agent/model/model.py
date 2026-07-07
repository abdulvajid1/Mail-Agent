from langchain_ollama import ChatOllama
from job_agent.config import MODEL_NAME


def load_model():
    # need to add exception there will be models that need reasoning
    model = ChatOllama(model=MODEL_NAME, reasoning=False)
    return model