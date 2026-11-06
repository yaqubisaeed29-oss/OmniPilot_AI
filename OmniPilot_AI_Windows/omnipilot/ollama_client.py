from __future__ import annotations
import base64, json, re
from pathlib import Path
import requests

class OllamaError(RuntimeError):
    pass

class OllamaClient:
    def __init__(self, base_url: str, timeout: int = 180):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
    def models(self) -> list[str]:
        try:
            r = requests.get(self.base_url + "/api/tags", timeout=8)
            r.raise_for_status()
            return [m.get("name", "") for m in r.json().get("models", [])]
        except requests.RequestException as e:
            raise OllamaError(f"Cannot reach Ollama at {self.base_url}: {e}") from e
    def generate(self, model: str, prompt: str, image: bytes | None = None) -> str:
        body = {"model": model, "prompt": prompt, "stream": False, "options": {"temperature": 0.15, "num_ctx": 8192}}
        if image is not None:
            body["images"] = [base64.b64encode(image).decode("ascii")]
        try:
            r = requests.post(self.base_url + "/api/generate", json=body, timeout=self.timeout)
            r.raise_for_status()
            text = r.json().get("response", "").strip()
            if not text:
                raise OllamaError("Ollama returned an empty response.")
            return text
        except requests.RequestException as e:
            raise OllamaError(f"Ollama request failed: {e}") from e
    @staticmethod
    def parse_json(text: str) -> dict:
        candidate = text.strip()
        candidate = re.sub(r"^```(?:json)?\s*|\s*```$", "", candidate, flags=re.I)
        try:
            value = json.loads(candidate)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", candidate, re.S)
            if not match:
                raise OllamaError("Model did not return valid JSON.")
            try:
                value = json.loads(match.group(0))
            except json.JSONDecodeError as e:
                raise OllamaError("Model returned malformed JSON.") from e
        if not isinstance(value, dict):
            raise OllamaError("Model response must be a JSON object.")
        return value
