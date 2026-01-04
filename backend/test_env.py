import os
print("=== Environment Variables Check ===")
print(f"OPENAI_API_KEY exists: {bool(os.environ.get('OPENAI_API_KEY'))}")
print(f"GOOGLE_API_KEY exists: {bool(os.environ.get('GOOGLE_API_KEY'))}")
print(f"SUPABASE_URL exists: {bool(os.environ.get('SUPABASE_URL'))}")
print(f"SUPABASE_KEY exists: {bool(os.environ.get('SUPABASE_KEY'))}")
print(f"Total env vars: {len(os.environ)}")
