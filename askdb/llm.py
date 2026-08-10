import os

import requests
from dotenv import load_dotenv

load_dotenv()

OLLAMA_URL = os.environ["OLLAMA_URL"]
OLLAMA_MODEL = os.environ["OLLAMA_MODEL"]


def generate(prompt: str) -> str:
    try:
        response = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0},
            },
        )
    except requests.exceptions.ConnectionError:
        raise RuntimeError(f"Could not reach Ollama at {OLLAMA_URL}. Is it running?")
    response.raise_for_status()
    return response.json()["response"]
