"""
Facebook Thread Parser Service
Uses LLM to parse full Facebook threads, extract Q&A pairs, and classify content
"""

import json
import time
from typing import List, Dict, Any, Tuple
from app.services.llm_adapters import get_adapter

# System prompt for thread parsing
THREAD_PARSER_SYSTEM_PROMPT = """You are an expert at parsing Facebook group discussions from Online Income Lab.

Your task is to analyze a Facebook thread (main post + all comment replies) and extract individual Q&A pairs.

CLASSIFICATION RULES:

1. MEANINGFUL Q&As:
   - Question asks for advice, explanation, or guidance
   - Answer provides substantial information, strategies, or insights
   - Educational value for business/entrepreneurship learning
   - Examples: pricing strategies, niche selection, marketing tactics, product development

2. FILLER content:
   - Short acknowledgments: "ok", "got it", "thanks", "noted", "haha"
   - Emoji-only or reaction-only: "👍", "🔥", "❤️"
   - Brief social pleasantries without educational content
   - Off-topic chit-chat
   - Questions without answers or answers without questions

EXTRACTION PROCESS:

1. Identify conversation structure:
   - Main post (first Q&A, depth=0)
   - Direct comment replies (depth=1)
   - Nested replies to comments (depth=2, 3, etc.)

2. For each Q&A pair, extract:
   - question: Clean question text (remove emojis, fix typos if obvious)
   - answer: Complete answer text
   - classification: "meaningful" or "filler"
   - confidence: 0.0-1.0 (how certain you are about classification)
   - reasoning: Brief explanation of classification (1 sentence)
   - tags: For meaningful Q&As only, extract 3-5 relevant tags
   - parent_index: Which Q&A this is replying to (null for main post)
   - depth: Nesting level (0=main, 1=direct reply, 2+=nested)

3. Output as JSON with this exact structure:
{
  "qa_pairs": [
    {
      "question": "the question text",
      "answer": "the answer text",
      "classification": "meaningful",
      "confidence": 0.95,
      "reasoning": "Substantive question with actionable answer",
      "tags": ["tag1", "tag2", "tag3"],
      "parent_index": null,
      "depth": 0
    }
  ]
}

HIERARCHY TRACKING:
- Each Q&A includes "parent_index" (which Q&A this is replying to)
- Main post has parent_index=null, depth=0
- Direct replies have parent_index=0 (replying to main post), depth=1
- Nested replies have parent_index=(index of parent comment), depth=2+
- This allows UI to display threaded conversation structure

IMPORTANT:
- Only extract pairs where BOTH question and answer are present
- **Be generous with "meaningful" classification** - when uncertain, classify as meaningful
- Confidence should reflect classification certainty, not answer quality
- Tags should be lowercase, 2-3 words max, business/niche topics
- Avoid generic tags like "business" or "online"
- Preserve chronological order within each depth level
- Return ONLY valid JSON, no additional text or explanation
"""


async def parse_facebook_thread(
    thread_text: str,
    source_url: str,
    provider: str = "openai"
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Parse Facebook thread using LLM

    Args:
        thread_text: Raw thread text (post + all comments)
        source_url: Facebook post URL
        provider: LLM provider ("openai" or "gemini")

    Returns:
        Tuple of:
        - List of parsed Q&A pairs with classifications
        - Metadata dict (model, tokens, cost, latency)

    Raises:
        Exception: If parsing fails or returns invalid JSON
    """
    start_time = time.time()

    # Get LLM adapter
    adapter = get_adapter(provider)

    # Create user prompt
    user_prompt = f"""Parse this Facebook thread and extract all Q&A pairs:

SOURCE URL: {source_url}

THREAD CONTENT:
{thread_text}

Extract all Q&A pairs following the classification rules. Return JSON only."""

    # Call LLM with increased max_tokens for thread parsing
    try:
        response_text, llm_metadata = await adapter.generate_answer(
            query=user_prompt,
            context="",  # No context needed for parsing
            system_prompt=THREAD_PARSER_SYSTEM_PROMPT,
            max_tokens=4000  # Increased limit for parsing multiple Q&As
        )

        # Debug: Log response length
        print(f"LLM response length: {len(response_text)} characters")

        # Parse JSON response with multiple fallback strategies
        import re
        parsed_json = None
        last_error = None

        # Strategy 1: Try direct parsing of full response
        try:
            parsed_json = json.loads(response_text.strip())
        except json.JSONDecodeError as e:
            last_error = f"Strategy 1 failed: {str(e)}"

        # Strategy 2: Extract from markdown code blocks (```json)
        if parsed_json is None and "```json" in response_text:
            try:
                extracted = response_text.split("```json")[1].split("```")[0].strip()
                print(f"Extracted JSON length: {len(extracted)} characters")
                parsed_json = json.loads(extracted)
            except (IndexError, json.JSONDecodeError) as e:
                last_error = f"Strategy 2 failed: {str(e)}"
                # Try Strategy 2b: Apply fixes to extracted JSON
                if not isinstance(e, IndexError):
                    try:
                        fixed = re.sub(r',(\s*[}\]])', r'\1', extracted)
                        parsed_json = json.loads(fixed)
                    except json.JSONDecodeError as e2:
                        print(f"Strategy 2b also failed: {str(e2)}")
                        print(f"Extracted JSON ends with: ...{extracted[-100:]}")

        # Strategy 3: Extract from any code block (```)
        if parsed_json is None and "```" in response_text:
            try:
                extracted = response_text.split("```")[1].split("```")[0].strip()
                # Remove potential "json" prefix
                if extracted.startswith("json"):
                    extracted = extracted[4:].strip()
                parsed_json = json.loads(extracted)
            except (IndexError, json.JSONDecodeError) as e:
                last_error = f"Strategy 3 failed: {str(e)}"
                # Try Strategy 3b: Apply fixes to extracted JSON
                if not isinstance(e, IndexError):
                    try:
                        fixed = re.sub(r',(\s*[}\]])', r'\1', extracted)
                        parsed_json = json.loads(fixed)
                    except json.JSONDecodeError:
                        pass

        # Strategy 4: Apply fixes to original response and retry
        if parsed_json is None:
            try:
                # Remove trailing commas before } or ]
                fixed = re.sub(r',(\s*[}\]])', r'\1', response_text.strip())
                # Fix single quotes to double quotes (risky but worth trying)
                fixed = fixed.replace("'", '"')
                parsed_json = json.loads(fixed)
            except json.JSONDecodeError as e:
                last_error = f"Strategy 4 failed: {str(e)}"

        # If all strategies fail, raise error with helpful message
        if parsed_json is None:
            error_msg = f"Failed to parse LLM response as JSON. Last error: {last_error}. Response length: {len(response_text)}. Response preview: {response_text[:1000]}..."
            raise Exception(error_msg)

        # Extract Q&A pairs
        qa_pairs = parsed_json.get("qa_pairs", [])

        # Validate structure
        if not isinstance(qa_pairs, list):
            raise Exception("Invalid response: qa_pairs must be a list")

        # Count classifications
        meaningful_count = sum(1 for qa in qa_pairs if qa.get("classification") == "meaningful")
        filler_count = sum(1 for qa in qa_pairs if qa.get("classification") == "filler")

        # Calculate latency
        latency_ms = int((time.time() - start_time) * 1000)

        # Build metadata
        metadata = {
            "model": llm_metadata.get("model", provider),
            "tokens_input": llm_metadata.get("tokens_in", 0),
            "tokens_output": llm_metadata.get("tokens_out", 0),
            "cost_usd": llm_metadata.get("cost", 0.0),
            "latency_ms": latency_ms,
            "provider": provider
        }

        return qa_pairs, metadata

    except Exception as e:
        # Log error and re-raise
        print(f"Thread parsing error: {str(e)}")
        raise Exception(f"Thread parsing failed: {str(e)}")


async def validate_parsed_qa(qa_dict: Dict[str, Any]) -> bool:
    """
    Validate a single parsed Q&A pair

    Args:
        qa_dict: Parsed Q&A dictionary

    Returns:
        True if valid, False otherwise
    """
    required_fields = ["question", "answer", "classification", "confidence"]

    # Check required fields
    for field in required_fields:
        if field not in qa_dict:
            return False

    # Validate types
    if not isinstance(qa_dict["question"], str) or not qa_dict["question"].strip():
        return False
    if not isinstance(qa_dict["answer"], str) or not qa_dict["answer"].strip():
        return False
    if qa_dict["classification"] not in ["meaningful", "filler"]:
        return False
    if not isinstance(qa_dict["confidence"], (int, float)) or not (0.0 <= qa_dict["confidence"] <= 1.0):
        return False

    # Optional fields with defaults
    qa_dict.setdefault("tags", [])
    qa_dict.setdefault("reasoning", "")
    qa_dict.setdefault("parent_index", None)
    qa_dict.setdefault("depth", 0)

    return True
