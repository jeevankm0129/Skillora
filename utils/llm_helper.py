import json

import requests

OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "mistral"


async def call_llm(prompt: str, expect_json: bool = False):
    """
    Calls Ollama local LLM.
    Works as a drop-in replacement for OpenAI.
    """

    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.2,
        },
    }

    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=120)
        response.raise_for_status()
    except Exception as e:
        raise RuntimeError(f"Ollama request failed: {e}")

    data = response.json()
    output = data.get("response", "").strip()

    if not output:
        raise ValueError("Ollama returned empty response")

    if expect_json:
        try:
            return json.loads(output)
        except json.JSONDecodeError:
            raise ValueError(f"Ollama did not return valid JSON.\nOutput:\n{output}")

    return output
