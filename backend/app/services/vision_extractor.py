"""
Vision Extraction Service
Handles screenshot Q&A extraction with fallback logic
"""

from typing import List, Dict, Any, Tuple, Optional
from app.services.llm_adapters import get_adapter


class VisionExtractionResult:
    """Container for vision extraction results"""

    def __init__(
        self,
        qa_pairs: List[Dict[str, Any]],
        confidence: float,
        model_used: str,
        metadata: Dict[str, Any],
        used_fallback: bool = False,
        warnings: List[str] = None,
    ):
        self.qa_pairs = qa_pairs
        self.confidence = confidence
        self.model_used = model_used
        self.metadata = metadata
        self.used_fallback = used_fallback
        self.warnings = warnings or []

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "qa_pairs": self.qa_pairs,
            "confidence": self.confidence,
            "model_used": self.model_used,
            "metadata": self.metadata,
            "used_fallback": self.used_fallback,
            "warnings": self.warnings,
        }


async def extract_from_screenshot(
    image_data: bytes,
    source_url: str,
    use_fallback: bool = True,
    confidence_threshold: float = 0.7,
    extraction_prompt: Optional[str] = None,
) -> VisionExtractionResult:
    """
    Extract Q&A pairs from screenshot with fallback logic

    Process:
    1. Try Gemini first (free, fast)
    2. If fails or confidence < threshold, try GPT-4 Vision
    3. Return best result

    Args:
        image_data: Raw image bytes
        source_url: URL of the Facebook post or source
        use_fallback: Whether to use GPT-4 fallback if Gemini fails
        confidence_threshold: Minimum confidence to accept result without fallback
        extraction_prompt: Optional custom prompt

    Returns:
        VisionExtractionResult with extracted Q&As, confidence, and metadata
    """
    warnings = []
    used_fallback = False

    # Try Gemini first (free tier)
    try:
        gemini_adapter = get_adapter("gemini")
        qa_pairs, confidence, metadata = await gemini_adapter.extract_from_image(
            image_data, source_url, extraction_prompt
        )

        # Validate extraction
        validation_warnings = validate_extraction_result(qa_pairs, confidence)
        warnings.extend(validation_warnings)

        # Check if result is acceptable
        if confidence >= confidence_threshold and len(qa_pairs) > 0:
            return VisionExtractionResult(
                qa_pairs=qa_pairs,
                confidence=confidence,
                model_used="gemini-vision",
                metadata=metadata,
                used_fallback=False,
                warnings=warnings,
            )
        else:
            # Low confidence or no results, try fallback
            if use_fallback:
                warnings.append(
                    f"Gemini extraction had low confidence ({confidence:.2f}) or no results, trying GPT-4 Vision fallback"
                )
            else:
                warnings.append(
                    f"Gemini extraction had low confidence ({confidence:.2f}) or no results, no fallback enabled"
                )
                return VisionExtractionResult(
                    qa_pairs=qa_pairs,
                    confidence=confidence,
                    model_used="gemini-vision",
                    metadata=metadata,
                    used_fallback=False,
                    warnings=warnings,
                )

    except Exception as e:
        # Gemini failed, try fallback
        if use_fallback:
            warnings.append(f"Gemini extraction failed: {str(e)}, trying GPT-4 Vision fallback")
        else:
            raise Exception(f"Gemini extraction failed and no fallback enabled: {str(e)}")

    # Fallback to GPT-4 Vision
    if use_fallback:
        try:
            openai_adapter = get_adapter("openai")
            qa_pairs, confidence, metadata = await openai_adapter.extract_from_image(
                image_data, source_url, extraction_prompt
            )

            used_fallback = True

            # Validate extraction
            validation_warnings = validate_extraction_result(qa_pairs, confidence)
            warnings.extend(validation_warnings)

            return VisionExtractionResult(
                qa_pairs=qa_pairs,
                confidence=confidence,
                model_used="gpt4-vision",
                metadata=metadata,
                used_fallback=True,
                warnings=warnings,
            )

        except Exception as e:
            raise Exception(f"Both Gemini and GPT-4 Vision extraction failed: {str(e)}")


def validate_extraction_result(
    qa_pairs: List[Dict[str, Any]], confidence: float
) -> List[str]:
    """
    Validate extraction quality and return warnings

    Args:
        qa_pairs: List of extracted Q&A pairs
        confidence: Overall confidence score

    Returns:
        List of warning messages
    """
    warnings = []

    # Check if no results
    if len(qa_pairs) == 0:
        warnings.append("No Q&A pairs extracted from image")
        return warnings

    # Check confidence score
    if confidence < 0.5:
        warnings.append(
            f"Low extraction confidence ({confidence:.2f}). Please review and edit carefully."
        )
    elif confidence < 0.7:
        warnings.append(
            f"Medium extraction confidence ({confidence:.2f}). Some manual review recommended."
        )

    # Validate individual Q&A pairs
    for i, qa in enumerate(qa_pairs):
        # Check required fields
        if "question" not in qa or not qa["question"]:
            warnings.append(f"Q&A pair {i+1}: Missing or empty question")

        if "answer" not in qa or not qa["answer"]:
            warnings.append(f"Q&A pair {i+1}: Missing or empty answer")

        # Check minimum length
        if "question" in qa and len(qa["question"]) < 10:
            warnings.append(f"Q&A pair {i+1}: Question seems too short (< 10 chars)")

        if "answer" in qa and len(qa["answer"]) < 20:
            warnings.append(f"Q&A pair {i+1}: Answer seems too short (< 20 chars)")

        # Check for generic/placeholder content
        generic_patterns = ["...", "[unclear]", "[missing]", "N/A", "n/a"]
        if "answer" in qa:
            for pattern in generic_patterns:
                if pattern in qa["answer"].lower():
                    warnings.append(
                        f"Q&A pair {i+1}: Answer contains placeholder text '{pattern}'"
                    )

    return warnings


async def extract_with_comparison(
    image_data: bytes, source_url: str, extraction_prompt: Optional[str] = None
) -> Tuple[VisionExtractionResult, VisionExtractionResult]:
    """
    Run both Gemini and GPT-4 Vision in parallel for comparison

    Useful for testing and quality comparison during development.
    Not recommended for production due to cost.

    Args:
        image_data: Raw image bytes
        source_url: URL of the source
        extraction_prompt: Optional custom prompt

    Returns:
        Tuple of (gemini_result, gpt4_result)
    """
    import asyncio

    # Run both extractions in parallel
    async def get_gemini_result():
        try:
            gemini_adapter = get_adapter("gemini")
            qa_pairs, confidence, metadata = await gemini_adapter.extract_from_image(
                image_data, source_url, extraction_prompt
            )
            warnings = validate_extraction_result(qa_pairs, confidence)
            return VisionExtractionResult(
                qa_pairs=qa_pairs,
                confidence=confidence,
                model_used="gemini-vision",
                metadata=metadata,
                used_fallback=False,
                warnings=warnings,
            )
        except Exception as e:
            return VisionExtractionResult(
                qa_pairs=[],
                confidence=0.0,
                model_used="gemini-vision",
                metadata={"error": str(e)},
                used_fallback=False,
                warnings=[f"Gemini extraction failed: {str(e)}"],
            )

    async def get_gpt4_result():
        try:
            openai_adapter = get_adapter("openai")
            qa_pairs, confidence, metadata = await openai_adapter.extract_from_image(
                image_data, source_url, extraction_prompt
            )
            warnings = validate_extraction_result(qa_pairs, confidence)
            return VisionExtractionResult(
                qa_pairs=qa_pairs,
                confidence=confidence,
                model_used="gpt4-vision",
                metadata=metadata,
                used_fallback=False,
                warnings=warnings,
            )
        except Exception as e:
            return VisionExtractionResult(
                qa_pairs=[],
                confidence=0.0,
                model_used="gpt4-vision",
                metadata={"error": str(e)},
                used_fallback=False,
                warnings=[f"GPT-4 Vision extraction failed: {str(e)}"],
            )

    gemini_result, gpt4_result = await asyncio.gather(
        get_gemini_result(), get_gpt4_result()
    )

    return gemini_result, gpt4_result
