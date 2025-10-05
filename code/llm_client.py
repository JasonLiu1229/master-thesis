import os
from dotenv import load_dotenv


class LLMClient:
    def __init__(self, api_key, base_url="https://api.openai.com/v1/chat/completions"):
        self.api_key = api_key
        self.base_url = base_url

    def chat(self, model, messages):
        import requests

        url = f"{self.base_url}/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        data = {"model": model, "messages": messages}
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]


if __name__ == "__main__":

    load_dotenv()

    API_KEY = os.getenv("API_KEY")
    API_URL = os.getenv("API_URL")

    client = LLMClient(API_KEY, API_URL)

    reply = client.chat(
        "gpt-4o-mini", [
            {"role": "user", "content": "Give me the time of today."},
            {"role": "system", "content": "You are a helpful assistant"}
            ]
    )

    print(reply)
