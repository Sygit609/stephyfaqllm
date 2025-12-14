#!/usr/bin/env python3
"""
CSV Import Script for OIL Q&A Tool
Imports Q&As from CSV and generates dual embeddings (OpenAI + Gemini)
"""

import os
import csv
import asyncio
from datetime import datetime
from typing import List, Dict, Optional
from dotenv import load_dotenv
import openai
import google.generativeai as genai
from supabase import create_client, Client

# Load environment variables
load_dotenv()

# Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Initialize clients
openai.api_key = OPENAI_API_KEY
genai.configure(api_key=GOOGLE_API_KEY)
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


class DualEmbeddingGenerator:
    """Generates embeddings using both OpenAI and Gemini"""

    def __init__(self):
        self.openai_client = openai.OpenAI(api_key=OPENAI_API_KEY)
        self.openai_model = "text-embedding-3-small"  # 1536 dimensions
        self.gemini_model = "models/text-embedding-004"  # 768 dimensions

    async def generate_openai_embedding(self, text: str) -> List[float]:
        """Generate OpenAI embedding"""
        try:
            response = self.openai_client.embeddings.create(
                model=self.openai_model, input=text
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"❌ OpenAI embedding error: {e}")
            return None

    async def generate_gemini_embedding(self, text: str) -> List[float]:
        """Generate Gemini embedding"""
        try:
            result = genai.embed_content(
                model=self.gemini_model,
                content=text,
                task_type="retrieval_document",
            )
            return result["embedding"]
        except Exception as e:
            print(f"❌ Gemini embedding error: {e}")
            return None

    async def generate_dual_embeddings(
        self, text: str
    ) -> tuple[Optional[List[float]], Optional[List[float]]]:
        """Generate both embeddings in parallel"""
        openai_task = self.generate_openai_embedding(text)
        gemini_task = self.generate_gemini_embedding(text)

        openai_emb, gemini_emb = await asyncio.gather(openai_task, gemini_task)
        return openai_emb, gemini_emb


def parse_csv_row(row: Dict) -> Dict:
    """Parse a CSV row into database format"""

    # Determine category from tags
    tags_str = row.get("tags", "")
    tags = [tag.strip() for tag in tags_str.split(",") if tag.strip()]

    # Simple category detection
    category = "internal"  # Default
    if any(tag in tags for tag in ["instagram", "facebook"]):
        category = "social_media"
    elif any(tag in tags for tag in ["funnel_freedom", "systeme"]):
        category = "tools"
    elif any(tag in tags for tag in ["email", "lead_magnet"]):
        category = "email_marketing"

    # Detect time-sensitive content (zoom links, schedules, etc.)
    is_time_sensitive = any(
        keyword in row.get("question_enriched", "").lower()
        or keyword in row.get("answer", "").lower()
        for keyword in ["zoom link", "today", "this week", "schedule", "upcoming"]
    )

    # Parse date
    try:
        date = datetime.strptime(row.get("date", ""), "%Y-%m-%d").date()
    except:
        date = datetime.now().date()

    return {
        "content_type": "qa",  # All current data is Q&A format
        "thread_id": row.get("thread_id"),
        "question_raw": row.get("question_raw"),
        "question_enriched": row.get("question_enriched"),
        "answer": row.get("answer"),
        "answered_by": row.get("answered_by"),
        "category": category,
        "tags": tags,
        "date": str(date),
        "is_time_sensitive": is_time_sensitive,
        "source": row.get("source", "fb_group"),
        "source_url": row.get("source_url"),
    }


async def import_csv_to_supabase(csv_path: str):
    """Main import function"""
    print(f"🚀 Starting CSV import from: {csv_path}")
    print(f"📊 Connecting to Supabase...")

    # Initialize embedding generator
    embedding_gen = DualEmbeddingGenerator()

    # Read CSV
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    print(f"📝 Found {len(rows)} rows in CSV")

    # Process each row
    success_count = 0
    error_count = 0

    for idx, row in enumerate(rows, 1):
        try:
            # Parse row
            parsed = parse_csv_row(row)

            # Skip if answer is pending or empty
            if not parsed["answer"] or "pending" in parsed["answer"].lower():
                print(f"⏭️  Row {idx}: Skipping pending answer")
                continue

            # Generate text for embedding (combine question + answer)
            embedding_text = f"{parsed['question_enriched'] or parsed['question_raw']}\n{parsed['answer']}"

            print(f"\n🔄 Processing row {idx}/{len(rows)}: {parsed['question_enriched'][:60]}...")

            # Generate embeddings
            openai_emb, gemini_emb = await embedding_gen.generate_dual_embeddings(
                embedding_text
            )

            if not openai_emb or not gemini_emb:
                print(f"⚠️  Row {idx}: Failed to generate embeddings, skipping")
                error_count += 1
                continue

            # Prepare data for insert
            insert_data = {
                **parsed,
                "embedding_openai": openai_emb,
                "embedding_gemini": gemini_emb,
                "embedding_generated_at": datetime.now().isoformat(),
            }

            # Insert into Supabase
            response = supabase.table("knowledge_items").insert(insert_data).execute()

            print(f"✅ Row {idx}: Imported successfully")
            success_count += 1

        except Exception as e:
            print(f"❌ Row {idx}: Error - {e}")
            error_count += 1

        # Small delay to avoid rate limits
        await asyncio.sleep(0.1)

    print(f"\n" + "=" * 60)
    print(f"✅ Import complete!")
    print(f"📊 Successfully imported: {success_count}")
    print(f"❌ Errors: {error_count}")
    print(f"📈 Total processed: {success_count + error_count}")
    print(f"=" * 60)


async def verify_import():
    """Verify the import by querying the database"""
    print(f"\n🔍 Verifying import...")

    try:
        response = supabase.table("knowledge_items").select("*").execute()
        count = len(response.data)
        print(f"✅ Found {count} records in database")

        if count > 0:
            # Show sample record
            sample = response.data[0]
            print(f"\n📄 Sample record:")
            print(f"   ID: {sample['id']}")
            print(f"   Question: {sample['question_enriched'][:80]}...")
            print(f"   Category: {sample['category']}")
            print(f"   Tags: {sample['tags']}")
            print(
                f"   OpenAI embedding dim: {len(sample.get('embedding_openai', []))}"
            )
            print(
                f"   Gemini embedding dim: {len(sample.get('embedding_gemini', []))}"
            )
    except Exception as e:
        print(f"❌ Verification error: {e}")


async def main():
    """Main entry point"""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python import_csv.py <path_to_csv>")
        print("Example: python import_csv.py ../Downloads/offerlab_qna.csv")
        sys.exit(1)

    csv_path = sys.argv[1]

    if not os.path.exists(csv_path):
        print(f"❌ CSV file not found: {csv_path}")
        sys.exit(1)

    # Check environment variables
    missing_vars = []
    for var in ["OPENAI_API_KEY", "GOOGLE_API_KEY", "SUPABASE_URL", "SUPABASE_KEY"]:
        if not os.getenv(var):
            missing_vars.append(var)

    if missing_vars:
        print(f"❌ Missing environment variables: {', '.join(missing_vars)}")
        print(f"Please create a .env file with these variables")
        sys.exit(1)

    # Run import
    await import_csv_to_supabase(csv_path)

    # Verify
    await verify_import()


if __name__ == "__main__":
    asyncio.run(main())
