"""
Video Transcription Service
Handles OpenAI Whisper API integration, transcript parsing, and segment creation
"""

import re
from typing import List, Dict, Optional, BinaryIO
from datetime import timedelta, date
import openai
from app.core.config import settings
from app.services.content_manager import generate_dual_embeddings
from supabase import Client


class TranscriptionService:
    """Service for transcribing videos and managing transcript segments"""

    def __init__(self):
        self.openai_client = openai.OpenAI(api_key=settings.openai_api_key)
        # Cost per minute for Whisper API
        self.whisper_cost_per_minute = 0.006

    async def transcribe_video(
        self,
        video_file: BinaryIO,
        language: str = "en"
    ) -> Dict:
        """
        Transcribe video using OpenAI Whisper API

        Args:
            video_file: Binary file object of the video
            language: Language code (e.g., 'en', 'es', 'fr')

        Returns:
            dict with 'srt_text', 'duration_seconds', 'cost_usd'
        """
        try:
            # Call Whisper API with SRT format
            response = self.openai_client.audio.transcriptions.create(
                model="whisper-1",
                file=video_file,
                response_format="srt",
                language=language
            )

            srt_text = response

            # Calculate duration and cost from SRT
            duration_seconds = self._calculate_duration_from_srt(srt_text)
            cost_usd = (duration_seconds / 60) * self.whisper_cost_per_minute

            return {
                "srt_text": srt_text,
                "duration_seconds": duration_seconds,
                "cost_usd": round(cost_usd, 4),
                "language": language,
                "format": "whisper"
            }

        except Exception as e:
            raise Exception(f"Whisper API transcription failed: {str(e)}")

    def parse_srt_to_segments(
        self,
        srt_text: str,
        segment_duration: int = 45
    ) -> List[Dict]:
        """
        Parse SRT format into logical segments

        Args:
            srt_text: SRT formatted transcript
            segment_duration: Target duration per segment in seconds (30-60s recommended)

        Returns:
            List of segments with start_time, end_time, text
        """
        # Parse SRT entries
        srt_entries = self._parse_srt_entries(srt_text)

        if not srt_entries:
            return []

        # Group into logical segments based on duration
        segments = []
        current_segment = {
            "start_time": srt_entries[0]["start_time"],
            "end_time": srt_entries[0]["end_time"],
            "text": srt_entries[0]["text"]
        }

        for i in range(1, len(srt_entries)):
            entry = srt_entries[i]
            segment_length = entry["end_time"] - current_segment["start_time"]

            # If adding this entry would exceed target duration, start new segment
            if segment_length >= segment_duration:
                # Look for natural break (sentence end)
                if self._is_natural_break(current_segment["text"]):
                    segments.append(current_segment)
                    current_segment = {
                        "start_time": entry["start_time"],
                        "end_time": entry["end_time"],
                        "text": entry["text"]
                    }
                else:
                    # Continue building current segment
                    current_segment["end_time"] = entry["end_time"]
                    current_segment["text"] += " " + entry["text"]
            else:
                # Add to current segment
                current_segment["end_time"] = entry["end_time"]
                current_segment["text"] += " " + entry["text"]

        # Add final segment
        if current_segment["text"]:
            segments.append(current_segment)

        return segments

    def parse_markdown_to_segments(self, markdown_content: str, segment_duration: int = 120) -> List[Dict]:
        """
        Parse markdown file into segments without timestamps.
        Splits content into logical chunks based on paragraphs and headings.

        Args:
            markdown_content: Raw markdown content
            segment_duration: Target segment duration (not used for markdown, kept for consistency)

        Returns:
            List of segments without timestamps
        """
        lines = markdown_content.strip().split('\n')
        segments = []
        current_text = ""

        for line in lines:
            line = line.strip()

            # Skip empty lines
            if not line:
                if current_text:
                    # Empty line signals end of paragraph
                    segments.append({
                        "start_time": None,
                        "end_time": None,
                        "text": current_text.strip()
                    })
                    current_text = ""
                continue

            # Heading - create segment for previous content and start fresh
            if line.startswith('#'):
                if current_text:
                    segments.append({
                        "start_time": None,
                        "end_time": None,
                        "text": current_text.strip()
                    })
                # Add heading as its own segment
                heading_text = line.lstrip('#').strip()
                if heading_text:
                    segments.append({
                        "start_time": None,
                        "end_time": None,
                        "text": heading_text
                    })
                current_text = ""
            else:
                # Regular line - add to current text
                if current_text:
                    current_text += " " + line
                else:
                    current_text = line

        # Add final segment if any
        if current_text:
            segments.append({
                "start_time": None,
                "end_time": None,
                "text": current_text.strip()
            })

        return segments

    def parse_uploaded_transcript(
        self,
        file_content: str,
        file_format: str
    ) -> List[Dict]:
        """
        Parse manually uploaded transcript file (.srt, .vtt, or .md)

        Args:
            file_content: Raw file content as string
            file_format: 'srt', 'vtt', or 'md'

        Returns:
            List of segments
        """
        if file_format == "srt":
            return self.parse_srt_to_segments(file_content)
        elif file_format == "vtt":
            # Convert VTT to SRT format first
            srt_text = self._convert_vtt_to_srt(file_content)
            return self.parse_srt_to_segments(srt_text)
        elif file_format == "md":
            # Parse markdown as plain text segments
            return self.parse_markdown_to_segments(file_content)
        else:
            raise ValueError(f"Unsupported transcript format: {file_format}")

    async def create_transcript_segments(
        self,
        lesson_id: str,
        course_id: str,
        module_id: str,
        segments: List[Dict],
        video_url: str,
        db: Client,
        lesson_name: str = "",
        module_name: str = "",
        course_name: str = ""
    ) -> List[str]:
        """
        Create transcript segment entries in database with dual embeddings

        Args:
            lesson_id: Parent lesson UUID
            course_id: Top-level course UUID
            module_id: Parent module UUID
            segments: List of parsed segments
            video_url: URL of the video
            db: Supabase client
            lesson_name, module_name, course_name: Names for context

        Returns:
            List of created segment IDs
        """
        created_ids = []

        for segment in segments:
            # Handle timestamps (None for markdown files, seconds for SRT/VTT)
            start_time = segment.get("start_time")
            end_time = segment.get("end_time")

            if start_time is not None:
                # Format timestamp for display
                start_mm_ss = self._seconds_to_mmss(start_time)
                # Generate embeddings with rich context including timestamp
                context_text = f"{course_name} - {module_name} - {lesson_name} ({start_mm_ss}): {segment['text']}"
                question_text = f"Transcript from {lesson_name} at {start_mm_ss}"
                content_type = "video"
            else:
                # No timestamp (markdown files)
                context_text = f"{course_name} - {module_name} - {lesson_name}: {segment['text']}"
                question_text = f"Content from {lesson_name}"
                content_type = "manual"  # Use 'manual' as it's allowed by DB constraint

            # Generate dual embeddings
            openai_embedding, gemini_embedding = await generate_dual_embeddings(context_text)

            # Create segment entry
            segment_data = {
                "content_type": content_type,
                "hierarchy_level": 4,  # Segment level
                "parent_id": lesson_id,
                "course_id": course_id,
                "module_id": module_id,
                "lesson_id": lesson_id,
                "question": question_text,
                "answer": segment["text"],
                "media_url": video_url if video_url else None,
                "timecode_start": start_time,
                "timecode_end": end_time,
                "date": date.today().isoformat(),  # Required field from original schema
                "embedding_openai": openai_embedding,
                "embedding_gemini": gemini_embedding,
                "extracted_by": "manual",  # Using 'manual' since 'whisper' not in DB constraint yet
                "extraction_confidence": 1.0,  # Transcript is accurate
            }

            result = db.table("knowledge_items").insert(segment_data).execute()
            created_ids.append(result.data[0]["id"])

        return created_ids

    def _parse_srt_entries(self, srt_text: str) -> List[Dict]:
        """Parse SRT format into individual entries"""
        entries = []

        # Split by double newlines (SRT entry separator)
        blocks = re.split(r'\n\s*\n', srt_text.strip())

        for block in blocks:
            lines = block.strip().split('\n')
            if len(lines) < 3:
                continue

            # Parse timestamp line (format: 00:00:10,500 --> 00:00:13,000)
            timestamp_match = re.search(
                r'(\d{2}):(\d{2}):(\d{2}),(\d{3})\s*-->\s*(\d{2}):(\d{2}):(\d{2}),(\d{3})',
                lines[1]
            )

            if not timestamp_match:
                continue

            # Convert to seconds
            start_time = (
                int(timestamp_match.group(1)) * 3600 +  # hours
                int(timestamp_match.group(2)) * 60 +    # minutes
                int(timestamp_match.group(3)) +         # seconds
                int(timestamp_match.group(4)) / 1000    # milliseconds
            )

            end_time = (
                int(timestamp_match.group(5)) * 3600 +
                int(timestamp_match.group(6)) * 60 +
                int(timestamp_match.group(7)) +
                int(timestamp_match.group(8)) / 1000
            )

            # Text is all lines after timestamp
            text = ' '.join(lines[2:]).strip()

            entries.append({
                "start_time": int(start_time),
                "end_time": int(end_time),
                "text": text
            })

        return entries

    def _calculate_duration_from_srt(self, srt_text: str) -> int:
        """Extract total duration from SRT file"""
        entries = self._parse_srt_entries(srt_text)
        if not entries:
            return 0
        return int(entries[-1]["end_time"])

    def _is_natural_break(self, text: str) -> bool:
        """Check if text ends with natural sentence break"""
        return text.rstrip().endswith(('.', '!', '?'))

    def _seconds_to_mmss(self, seconds: int) -> str:
        """Convert seconds to MM:SS format"""
        minutes = seconds // 60
        secs = seconds % 60
        return f"{minutes:02d}:{secs:02d}"

    def _convert_vtt_to_srt(self, vtt_text: str) -> str:
        """Convert VTT format to SRT format"""
        # Remove VTT header
        srt_text = re.sub(r'^WEBVTT\n\n', '', vtt_text)

        # Replace VTT timestamp format (00:00:10.500) with SRT format (00:00:10,500)
        srt_text = re.sub(r'(\d{2}):(\d{2}):(\d{2})\.(\d{3})', r'\1:\2:\3,\4', srt_text)

        # Add sequence numbers (VTT doesn't require them, SRT does)
        blocks = re.split(r'\n\s*\n', srt_text.strip())
        numbered_blocks = []
        for i, block in enumerate(blocks, 1):
            numbered_blocks.append(f"{i}\n{block}")

        return '\n\n'.join(numbered_blocks)


# Singleton instance
transcription_service = TranscriptionService()
