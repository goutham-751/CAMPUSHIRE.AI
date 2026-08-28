import logging

logger = logging.getLogger("campushire.database")

try:
    from supabase import create_client, Client
except ImportError:  # pragma: no cover
    create_client = None
    Client = None

from backend.config import settings


def get_supabase_client():
    """Initialize and return the Supabase client (service role — backend only)."""
    if create_client is None:
        logger.warning("supabase package is not installed. Database operations will be skipped.")
        return None

    if not settings.SUPABASE_URL or not settings.SUPABASE_KEY:
        logger.warning("Supabase URL or Key is missing. Database operations will be skipped.")
        return None

    try:
        return create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
    except Exception as e:
        logger.error("Failed to initialize Supabase client: %s", e)
        return None


supabase = get_supabase_client()
