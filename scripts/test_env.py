#!/usr/bin/env python3
"""Test if .env file is loaded correctly"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Get the project root (parent of scripts directory)
project_root = Path(__file__).parent.parent
env_path = project_root / '.env'

print(f"Looking for .env at: {env_path}")
print(f".env exists: {env_path.exists()}")

# Load .env from project root
load_dotenv(env_path)

print("Testing .env file loading...")
print(f"SUPABASE_URL: {os.getenv('SUPABASE_URL')}")
print(f"SUPABASE_KEY length: {len(os.getenv('SUPABASE_KEY', ''))} chars")
print(f"SUPABASE_KEY starts with: {os.getenv('SUPABASE_KEY', '')[:20]}...")
print(f"OPENAI_API_KEY length: {len(os.getenv('OPENAI_API_KEY', ''))} chars")
print(f"GOOGLE_API_KEY length: {len(os.getenv('GOOGLE_API_KEY', ''))} chars")
