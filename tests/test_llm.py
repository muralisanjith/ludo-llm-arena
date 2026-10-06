import unittest
from arena.llm import LLM, GeminiLLM, GroqLLM, OpenRouterLLM


class TestLLM(unittest.TestCase):
    def test_all_model_names(self):
        models = LLM.all_model_names()
        self.assertIn("gemini-2.5-flash", models)
        self.assertIn("gpt-oss-20b (Groq)", models)
        self.assertIn("gpt-oss-120b (Groq)", models)
        self.assertIn("gpt-oss-120b (OpenRouter)", models)

    def test_factory_creation(self):
        gemini = LLM.create("gemini-2.5-flash")
        self.assertIsInstance(gemini, GeminiLLM)

        groq_20b = LLM.create("gpt-oss-20b (Groq)")
        self.assertIsInstance(groq_20b, GroqLLM)
        self.assertEqual(groq_20b.model, "openai/gpt-oss-20b")

        groq_120b = LLM.create("gpt-oss-120b (Groq)")
        self.assertIsInstance(groq_120b, GroqLLM)

        openrouter = LLM.create("gpt-oss-120b (OpenRouter)")
        self.assertIsInstance(openrouter, OpenRouterLLM)


if __name__ == "__main__":
    unittest.main()
