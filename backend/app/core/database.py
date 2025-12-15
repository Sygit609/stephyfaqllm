"""
Database Client
Initializes and manages Supabase connection
"""

from typing import Optional
from supabase import create_client, Client
from app.core.config import settings


class DatabaseClient:
    """Supabase database client wrapper"""

    def __init__(self):
        self._client: Optional[Client] = None

    def connect(self) -> Client:
        """Initialize Supabase client"""
        if not self._client:
            self._client = create_client(settings.supabase_url, settings.supabase_key)
        return self._client

    def disconnect(self):
        """Cleanup database connection"""
        self._client = None

    @property
    def client(self) -> Client:
        """Get the Supabase client instance"""
        if not self._client:
            self.connect()
        return self._client


# Global database instance
db = DatabaseClient()


def get_db() -> Client:
    """
    Dependency function for FastAPI endpoints
    Returns Supabase client
    """
    return db.client
