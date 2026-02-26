import asyncio
import json
from typing import Any, Union

import httpx

from config import HF_API_TOKEN, HF_MODEL

BASE_URL = "https://router.huggingface.co/v1"
TIMEOUT = 90
RETRIES = 2


def _safe_json_parse(output: str) -> Any:
    output = output.strip()

    # Direct JSON
    try:
        return json.loads(output)
    except json.JSONDecodeError:
        pass

    # Extract first {...} or [...]
    obj_start = output.find("{")
    obj_end = output.rfind("}") + 1
    arr_start = output.find("[")
    arr_end = output.rfind("]") + 1

    candidates = []
    if obj_start != -1 and obj_end > obj_start:
        candidates.append(output[obj_start:obj_end])
    if arr_start != -1 and arr_end > arr_start:
        candidates.append(output[arr_start:arr_end])

    for c in candidates:
        try:
            return json.loads(c)
        except json.JSONDecodeError:
            continue

    raise ValueError(f"Invalid JSON returned by model. Output:\n{output[:800]}")


def _model_for_hf_inference(model_id: str) -> str:
    # For hf-inference provider, router expects "model:provider"
    # If user already set a provider suffix, keep it.
    if ":" in model_id:
        return model_id
    return f"{model_id}:hf-inference"


async def call_llm(prompt: str, expect_json: bool = False) -> Union[str, Any]:
    """
    HuggingFace Inference Providers via OpenAI-compatible Chat Completions.
    """
    headers = {
        "Authorization": f"Bearer {HF_API_TOKEN}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": _model_for_hf_inference(HF_MODEL),
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.2,
        "max_tokens": 800,
        "stream": False,
    }

    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        for attempt in range(RETRIES):
            try:
                resp = await client.post(
                    f"{BASE_URL}/chat/completions", headers=headers, json=payload
                )

                if resp.status_code >= 400:
                    raise RuntimeError(f"HF error {resp.status_code}: {resp.text[:600]}")

                data = resp.json()
                # OpenAI-compatible shape
                output = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                output = str(output).strip()

                if not output:
                    raise ValueError("Empty response from HuggingFace")

                if expect_json:
                    return _safe_json_parse(output)

                return output

            except Exception as e:
                if attempt == RETRIES - 1:
                    raise RuntimeError(f"HuggingFace call failed: {e}")
                await asyncio.sleep(1)
