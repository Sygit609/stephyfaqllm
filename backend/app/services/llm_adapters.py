"""
LLM Adapter Pattern
Provides unified interface for OpenAI and Gemini models
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Tuple
import openai
import google.generativeai as genai
from app.core.config import settings


class BaseLLMAdapter(ABC):
    """Abstract base class for LLM providers"""

    def __init__(self):
        self.provider_name = "base"

    @abstractmethod
    async def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding vector for text"""
        pass

    @abstractmethod
    async def generate_answer(
        self, query: str, context: str, system_prompt: str
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Generate answer given query and context
        Returns: (answer_text, metadata_dict)
        metadata includes: tokens_input, tokens_output, model, latency_ms
        """
        pass

    @abstractmethod
    def calculate_cost(self, tokens_input: int, tokens_output: int) -> float:
        """Calculate cost in USD for the generation"""
        pass


class OpenAIAdapter(BaseLLMAdapter):
    """OpenAI implementation using gpt-4o and text-embedding-3-small"""

    def __init__(self):
        super().__init__()
        self.provider_name = "openai"
        self.client = openai.OpenAI(api_key=settings.openai_api_key)
        self.embedding_model = settings.openai_embedding_model
        self.generation_model = settings.openai_generation_model

    async def generate_embedding(self, text: str) -> List[float]:
        """Generate OpenAI embedding (1536 dimensions)"""
        try:
            response = self.client.embeddings.create(
                model=self.embedding_model, input=text
            )
            return response.data[0].embedding
        except Exception as e:
            raise Exception(f"OpenAI embedding error: {e}")

    async def generate_answer(
        self, query: str, context: str, system_prompt: str
    ) -> Tuple[str, Dict[str, Any]]:
        """Generate answer using gpt-4o"""
        import time

        start_time = time.time()

        try:
            response = self.client.chat.completions.create(
                model=self.generation_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {query}"},
                ],
                temperature=0.7,
                max_tokens=500,
            )

            latency_ms = int((time.time() - start_time) * 1000)
            answer = response.choices[0].message.content
            tokens_input = response.usage.prompt_tokens
            tokens_output = response.usage.completion_tokens

            metadata = {
                "model": self.generation_model,
                "tokens_input": tokens_input,
                "tokens_output": tokens_output,
                "latency_ms": latency_ms,
                "cost_usd": self.calculate_cost(tokens_input, tokens_output),
            }

            return answer, metadata

        except Exception as e:
            raise Exception(f"OpenAI generation error: {e}")

    def calculate_cost(self, tokens_input: int, tokens_output: int) -> float:
        """Calculate OpenAI cost"""
        input_cost = (tokens_input / 1000) * settings.openai_input_cost
        output_cost = (tokens_output / 1000) * settings.openai_output_cost
        return round(input_cost + output_cost, 6)


class GeminiAdapter(BaseLLMAdapter):
    """Google Gemini implementation using Gemini 2.0 Flash"""

    def __init__(self):
        super().__init__()
        self.provider_name = "gemini"
        genai.configure(api_key=settings.google_api_key)
        self.embedding_model = settings.gemini_embedding_model
        self.generation_model = settings.gemini_generation_model

    async def generate_embedding(self, text: str) -> List[float]:
        """Generate Gemini embedding (768 dimensions)"""
        try:
            result = genai.embed_content(
                model=self.embedding_model, content=text, task_type="retrieval_query"
            )
            return result["embedding"]
        except Exception as e:
            raise Exception(f"Gemini embedding error: {e}")

    async def generate_answer(
        self, query: str, context: str, system_prompt: str
    ) -> Tuple[str, Dict[str, Any]]:
        """Generate answer using Gemini 2.0 Flash"""
        import time

        start_time = time.time()

        try:
            model = genai.GenerativeModel(
                model_name=self.generation_model,
                system_instruction=system_prompt,
            )

            prompt = f"Context:\n{context}\n\nQuestion: {query}"
            response = model.generate_content(prompt)

            latency_ms = int((time.time() - start_time) * 1000)
            answer = response.text

            # Gemini doesn't provide exact token counts, estimate from text
            tokens_input = len(prompt.split()) * 1.3  # Rough estimate
            tokens_output = len(answer.split()) * 1.3

            metadata = {
                "model": self.generation_model,
                "tokens_input": int(tokens_input),
                "tokens_output": int(tokens_output),
                "latency_ms": latency_ms,
                "cost_usd": 0.0,  # Free within quota
            }

            return answer, metadata

        except Exception as e:
            raise Exception(f"Gemini generation error: {e}")

    def calculate_cost(self, tokens_input: int, tokens_output: int) -> float:
        """Gemini is free within quota"""
        return 0.0


def get_adapter(provider: str) -> BaseLLMAdapter:
    """
    Factory function to get the appropriate LLM adapter
    Args:
        provider: 'openai' or 'gemini'
    Returns:
        LLM adapter instance
    """
    provider = provider.lower()

    if provider == "openai":
        return OpenAIAdapter()
    elif provider == "gemini":
        return GeminiAdapter()
    else:
        raise ValueError(
            f"Unknown provider: {provider}. Must be 'openai' or 'gemini'"
        )
