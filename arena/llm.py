import os
from abc import ABC, abstractmethod
from dotenv import load_dotenv

load_dotenv()


class LLM(ABC):
    def __init__(self, model: str):
        self.model = model

    @abstractmethod
    def chat(self, system: str, user: str, max_tokens: int = 600) -> str:
        pass

    @classmethod
    def all_model_names(cls):
        return [
            "gemini-2.5-flash",
            "gpt-oss-20b (Groq)",
            "gpt-oss-120b (Groq)",
            "gpt-oss-120b (OpenRouter)"
        ]

    @classmethod
    def create(cls, model_name: str) -> "LLM":
        if model_name == "gemini-2.5-flash":
            return GeminiLLM("gemini-2.5-flash")
        elif model_name == "gpt-oss-20b (Groq)":
            return GroqLLM("openai/gpt-oss-20b")
        elif model_name == "gpt-oss-120b (Groq)":
            return GroqLLM("openai/gpt-oss-120b")
        elif model_name == "gpt-oss-120b (OpenRouter)":
            return OpenRouterLLM("openai/gpt-oss-120b")
        else:
            if "groq" in model_name.lower():
                return GroqLLM(model_name)
            elif "openrouter" in model_name.lower():
                return OpenRouterLLM(model_name)
            elif "gemini" in model_name.lower():
                return GeminiLLM(model_name)
            raise ValueError(f"Unknown model name: {model_name}")


class GeminiLLM(LLM):
    def __init__(self, model: str = "gemini-2.5-flash"):
        super().__init__(model)
        self.api_key = os.getenv("GOOGLE_API_KEY")

    def chat(self, system: str, user: str, max_tokens: int = 600) -> str:
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY environment variable is not set.")

        try:
            from google import genai
            from google.genai import types
            client = genai.Client(api_key=self.api_key)
            prompt = f"{system}\n\n{user}"
            response = client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=types.GenerateContentConfig(max_output_tokens=max_tokens)
            )
            return response.text
        except Exception as e:
            try:
                from openai import OpenAI
                client = OpenAI(
                    api_key=self.api_key,
                    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
                )
                response = client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system},
                        {"role": "user", "content": user}
                    ],
                    max_tokens=max_tokens
                )
                return response.choices[0].message.content
            except Exception:
                raise e


class GroqLLM(LLM):
    def __init__(self, model: str):
        super().__init__(model)
        self.api_key = os.getenv("GROQ_API_KEY")

    def chat(self, system: str, user: str, max_tokens: int = 600) -> str:
        if not self.api_key:
            raise ValueError("GROQ_API_KEY environment variable is not set.")

        try:
            from groq import Groq
            client = Groq(api_key=self.api_key)
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user}
                ],
                max_tokens=max_tokens
            )
            return response.choices[0].message.content
        except Exception as e:
            try:
                from openai import OpenAI
                client = OpenAI(
                    api_key=self.api_key,
                    base_url="https://api.groq.com/openai/v1"
                )
                response = client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system},
                        {"role": "user", "content": user}
                    ],
                    max_tokens=max_tokens
                )
                return response.choices[0].message.content
            except Exception:
                raise e


class OpenRouterLLM(LLM):
    def __init__(self, model: str):
        super().__init__(model)
        self.api_key = os.getenv("OPENROUTER_API_KEY")

    def chat(self, system: str, user: str, max_tokens: int = 600) -> str:
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY environment variable is not set.")

        from openai import OpenAI
        client = OpenAI(
            api_key=self.api_key,
            base_url="https://openrouter.ai/api/v1"
        )
        response = client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user}
            ],
            max_tokens=max_tokens
        )
        return response.choices[0].message.content
