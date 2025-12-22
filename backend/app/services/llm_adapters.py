"""
LLM Adapter Pattern
Provides unified interface for OpenAI and Gemini models
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Tuple, Optional
import base64
import openai
import google.generativeai as genai
from PIL import Image
import io
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

    @abstractmethod
    async def extract_from_image(
        self, image_data: bytes, source_url: str, extraction_prompt: Optional[str] = None
    ) -> Tuple[List[Dict[str, Any]], float, Dict[str, Any]]:
        """
        Extract Q&A pairs from screenshot image
        Args:
            image_data: Raw image bytes
            source_url: URL of the source (for metadata)
            extraction_prompt: Optional custom prompt for extraction
        Returns:
            Tuple of:
            - List of Q&A dictionaries with keys: question, answer, tags (optional)
            - Confidence score (0.0 to 1.0)
            - Metadata dict: model, latency_ms, cost_usd, tokens, etc.
        """
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

    async def extract_from_image(
        self, image_data: bytes, source_url: str, extraction_prompt: Optional[str] = None
    ) -> Tuple[List[Dict[str, Any]], float, Dict[str, Any]]:
        """Extract Q&A pairs using GPT-4 Vision (gpt-4o supports vision)"""
        import time
        import json

        start_time = time.time()

        # Default extraction prompt
        if extraction_prompt is None:
            extraction_prompt = """You are an expert at extracting Q&A content from Facebook group screenshots.

Analyze this screenshot and extract all question-answer pairs visible in the image.

For each Q&A pair, provide:
1. The question (clean, concise)
2. The answer (complete, accurate)
3. Relevant tags (comma-separated, e.g., "pricing, digital products, business")

Return your response as a JSON object with this structure:
{
  "qa_pairs": [
    {
      "question": "the question text",
      "answer": "the answer text",
      "tags": ["tag1", "tag2", "tag3"]
    }
  ],
  "confidence": 0.95,
  "notes": "any extraction notes or warnings"
}

IMPORTANT:
- Only extract complete Q&A pairs (both question AND answer must be present)
- Skip partial content, comments without answers, or unclear text
- Confidence should reflect extraction quality (0.0 to 1.0)
- If you're unsure about content, lower the confidence score
- Tags should be specific and relevant to Online Income Lab topics"""

        try:
            # Encode image as base64
            base64_image = base64.b64encode(image_data).decode('utf-8')

            response = self.client.chat.completions.create(
                model="gpt-4o",  # gpt-4o supports vision
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": extraction_prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}",
                                    "detail": "high"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=1500,
                temperature=0.3,  # Lower temp for more consistent extraction
            )

            latency_ms = int((time.time() - start_time) * 1000)
            result_text = response.choices[0].message.content

            # Parse JSON response
            try:
                # Try to extract JSON from response (handle markdown code blocks)
                if "```json" in result_text:
                    json_str = result_text.split("```json")[1].split("```")[0].strip()
                elif "```" in result_text:
                    json_str = result_text.split("```")[1].split("```")[0].strip()
                else:
                    json_str = result_text

                result_data = json.loads(json_str)
                qa_pairs = result_data.get("qa_pairs", [])
                confidence = result_data.get("confidence", 0.5)

            except json.JSONDecodeError:
                # Fallback if JSON parsing fails
                qa_pairs = []
                confidence = 0.0

            tokens_input = response.usage.prompt_tokens
            tokens_output = response.usage.completion_tokens

            # Vision API has higher costs
            vision_cost = self.calculate_cost(tokens_input, tokens_output)

            metadata = {
                "model": "gpt-4o-vision",
                "tokens_input": tokens_input,
                "tokens_output": tokens_output,
                "latency_ms": latency_ms,
                "cost_usd": vision_cost,
                "source_url": source_url,
                "raw_response": result_text
            }

            return qa_pairs, confidence, metadata

        except Exception as e:
            raise Exception(f"OpenAI vision extraction error: {e}")


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

    async def extract_from_image(
        self, image_data: bytes, source_url: str, extraction_prompt: Optional[str] = None
    ) -> Tuple[List[Dict[str, Any]], float, Dict[str, Any]]:
        """Extract Q&A pairs using Gemini Vision"""
        import time
        import json

        start_time = time.time()

        # Default extraction prompt
        if extraction_prompt is None:
            extraction_prompt = """You are an expert at extracting Q&A content from Facebook group screenshots.

Analyze this screenshot and extract all question-answer pairs visible in the image.

For each Q&A pair, provide:
1. The question (clean, concise)
2. The answer (complete, accurate)
3. Relevant tags (comma-separated, e.g., "pricing, digital products, business")

Return your response as a JSON object with this structure:
{
  "qa_pairs": [
    {
      "question": "the question text",
      "answer": "the answer text",
      "tags": ["tag1", "tag2", "tag3"]
    }
  ],
  "confidence": 0.95,
  "notes": "any extraction notes or warnings"
}

IMPORTANT:
- Only extract complete Q&A pairs (both question AND answer must be present)
- Skip partial content, comments without answers, or unclear text
- Confidence should reflect extraction quality (0.0 to 1.0)
- If you're unsure about content, lower the confidence score
- Tags should be specific and relevant to Online Income Lab topics"""

        try:
            # Convert bytes to PIL Image
            image = Image.open(io.BytesIO(image_data))

            # Use Gemini 2.0 Flash with vision
            model = genai.GenerativeModel(model_name="gemini-2.0-flash-exp")

            response = model.generate_content([extraction_prompt, image])

            latency_ms = int((time.time() - start_time) * 1000)
            result_text = response.text

            # Parse JSON response
            try:
                # Try to extract JSON from response (handle markdown code blocks)
                if "```json" in result_text:
                    json_str = result_text.split("```json")[1].split("```")[0].strip()
                elif "```" in result_text:
                    json_str = result_text.split("```")[1].split("```")[0].strip()
                else:
                    json_str = result_text

                result_data = json.loads(json_str)
                qa_pairs = result_data.get("qa_pairs", [])
                confidence = result_data.get("confidence", 0.5)

            except json.JSONDecodeError:
                # Fallback if JSON parsing fails
                qa_pairs = []
                confidence = 0.0

            # Estimate tokens
            tokens_input = len(extraction_prompt.split()) * 1.3
            tokens_output = len(result_text.split()) * 1.3

            metadata = {
                "model": "gemini-2.0-flash-vision",
                "tokens_input": int(tokens_input),
                "tokens_output": int(tokens_output),
                "latency_ms": latency_ms,
                "cost_usd": 0.0,  # Free within quota
                "source_url": source_url,
                "raw_response": result_text
            }

            return qa_pairs, confidence, metadata

        except Exception as e:
            raise Exception(f"Gemini vision extraction error: {e}")


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
