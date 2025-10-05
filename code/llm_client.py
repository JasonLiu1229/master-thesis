class LLMClient:
    def __init__(self, api_key, base_url="https://api.openai.com/v1"):
        self.api_key = api_key
        self.base_url = base_url

    def chat(self, model, messages):
        import requests
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        data = {"model": model, "messages": messages}
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
