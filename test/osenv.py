import os

api_base = os.environ.get("OPENAI_API_BASE", "https://api.openai.com/v1")
print(api_base)