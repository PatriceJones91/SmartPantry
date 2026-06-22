import os
from functools import lru_cache
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

@lru_cache
def get_supabase() -> Client:
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    if not url or not key:
        raise RuntimeError("Missing Supabase settings. Add SUPABASE_URL and SUPABASE_KEY to backend/.env.")
    return create_client(url, key)

def table(name: str):
    return get_supabase().table(name)

def rows(response):
    return response.data or []

def row(response):
    data = response.data or []
    return data[0] if data else None
