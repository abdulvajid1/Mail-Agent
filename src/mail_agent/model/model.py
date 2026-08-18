import os

from mail_agent.utils import load_config

PROVIDERS = {
    "ollama": {
        "name": "Ollama (Local)",
        "requires_api_key": False,
        "env_key": None,
    },
    "groq": {
        "name": "Groq (Cloud)",
        "requires_api_key": True,
        "env_key": "GROQ_API_KEY",
    },
    "openrouter": {
        "name": "OpenRouter (Cloud)",
        "requires_api_key": True,
        "env_key": "OPENROUTER_API_KEY",
    },
    "huggingfacehub": {
        "name": "Hugging Face Hub (Cloud)",
        "requires_api_key": True,
        "env_key": "HUGGINGFACEHUB_API_TOKEN",
    },
}


def _get_env_key(provider: str) -> str | None:
    env_key = PROVIDERS.get(provider, {}).get("env_key")
    return os.getenv(env_key) if env_key else None


def load_model(model_name: str | None = None, provider: str | None = None):
    config = load_config()
    provider = provider or config.get("provider", "ollama")
    model_name = model_name or config.get("model")

    if not model_name:
        raise ValueError("No model configured. Run `mail-agent setup` first.")

    if provider == "ollama":
        from langchain_ollama import ChatOllama

        return ChatOllama(model=model_name, reasoning=False)  # type: ignore

    elif provider == "groq":
        from langchain_groq import ChatGroq

        api_key = _get_env_key("groq")
        if not api_key:
            raise ValueError(
                "GROQ_API_KEY not set. Add it to your .env or export it in your shell."
            )
        return ChatGroq(model=model_name, api_key=api_key)

    elif provider == "openrouter":
        from langchain_openai import ChatOpenAI

        api_key = _get_env_key("openrouter")
        if not api_key:
            raise ValueError(
                "OPENROUTER_API_KEY not set. Add it to your .env or export it in your shell."
            )
        return ChatOpenAI(
            model=model_name,
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1",
        )
    
    elif provider == "huggingfacehub":
        from langchain_openai import ChatOpenAI

        api_key = _get_env_key("huggingfacehub")
        if not api_key:
            raise ValueError(
                "HUGGINGFACEHUB_API_TOKEN not set. Add it to your .env or export it in your shell."
            )
        
        # llm = HuggingFaceEndpoint(
        #     repo=model_name, 
        #     task="text-generation",
        #     provider='auto', 
        #     huggingfacehub_api_token=api_key, 
        #     streaming=True,
        # )

        # return ChatHuggingFace(llm=llm)
        return ChatOpenAI(
            base_url="https://router.huggingface.co/v1",
            api_key=api_key,
            model_name=model_name
        )

    else:
        raise ValueError(
            f"Unknown provider: {provider}. Choose from: {', '.join(PROVIDERS)}"
        )
