import os

import requests
from dotenv import load_dotenv

# Force load from current directory
load_dotenv(dotenv_path=".env")

print("Loaded token:", os.getenv("HF_API_TOKEN"))

HF_API_TOKEN = os.getenv("HF_API_TOKEN")

API_URL = "https://router.huggingface.co/hf-inference/models/dslim/bert-base-NER"

headers = {"Authorization": f"Bearer {HF_API_TOKEN}", "Content-Type": "application/json"}

text = "John is a Python developer with experience in Django, AWS and SQL."

response = requests.post(API_URL, headers=headers, json={"inputs": text}, timeout=30)

print("Status:", response.status_code)
print("Response:", response.json())
