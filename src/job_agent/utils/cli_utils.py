import urllib.request
import urllib.error

def is_ollama_running(url="http://localhost:11434"):
    try:
        # Send a request to the default Ollama local server
        response = urllib.request.urlopen(url, timeout=2)
        if response.status == 200:
            return True
    except urllib.error.URLError:
        # Server is not running or port is closed
        return False