import urllib.request
import urllib.error
from pathlib import Path
import json

from job_agent.config import CONFIG_PATH

def is_ollama_running(url="http://localhost:11434"):
    try:
        # Send a request to the default Ollama local server
        response = urllib.request.urlopen(url, timeout=2)
        if response.status == 200:
            return True
    except urllib.error.URLError:
        # Server is not running or port is closed
        return False


def load_config():
    config_dir = Path.home() / '.agent'
    config_dir.mkdir(exist_ok=True, parents=True)
    config_file = config_dir / 'config.json'

    # if there is no config file, create one with defualt value
    if not config_file.exists():
        agent_config = {
            "enabled_tools": [],
            "mail_authorization": False,
            "model": ""
        }

        with open(config_file, 'w') as f:
           json.dump(agent_config, f)
        
        return agent_config
    
    with open(config_file, 'r') as f:
        agent_config = json.load(f)
    
    return agent_config


def save_config(config: dict):
    with open(CONFIG_PATH, 'w') as f:
        json.dump(config, f)
    
