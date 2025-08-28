import httpx


class OllamaClient:
    def __init__(self, host: str = "http://localhost:11434"):
        self.base_url = host

    async def list_models(self) -> list:
        url = f"{self.base_url}/api/tags"
        async with httpx.AsyncClient(timeout=30) as client:
            try:
                response = await client.get(url)
                response.raise_for_status()
                return response.json().get("models", [])
            except Exception as e:
                raise Exception(f"Failed to list Ollama models: {e}")

    async def chat(self, prompt: str, model: str = "llama3") -> str:
        url = f"{self.base_url}/api/generate"
        payload = {"model": model, "prompt": prompt, "stream": False}
        async with httpx.AsyncClient(timeout=120) as client:
            try:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                return response.json().get("response", "")
            except Exception as e:
                raise Exception(f"Failed to get response from Ollama model {model}: {e}")
