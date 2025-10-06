"""Database package for Supabase integration."""

from .supabase_service import SupabaseService, get_supabase_service

__all__ = ["SupabaseService", "get_supabase_service"]
