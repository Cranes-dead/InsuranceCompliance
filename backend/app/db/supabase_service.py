"""
Supabase database service for policy storage.
Replaces in-memory storage with persistent database.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
import os
from supabase import create_client, Client
from uuid import UUID

from app.core import get_logger

logger = get_logger(__name__)


class SupabaseService:
    """Service for interacting with Supabase database."""
    
    def __init__(self):
        """Initialize Supabase client."""
        self.url = os.getenv("SUPABASE_URL", "https://ruwnawyecvazilaqseca.supabase.co")
        self.key = os.getenv("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJ1d25hd3llY3ZhemlsYXFzZWNhIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTkzOTUyNDcsImV4cCI6MjA3NDk3MTI0N30.OzLULXSN4b_ly3wYa6RiZmYXBYj-y-2eFgZ6-fsy3B4")
        self.client: Client = create_client(self.url, self.key)
        logger.info("✅ Supabase client initialized")
    
    # ============= POLICY OPERATIONS =============
    
    async def create_policy(self, policy_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new policy in database.
        
        Args:
            policy_data: Policy data with all fields
            
        Returns:
            Created policy data with ID
        """
        try:
            # Ensure proper data types
            data = {
                "id": str(policy_data.get("id")),
                "filename": policy_data["filename"],
                "classification": policy_data["classification"],
                "confidence": float(policy_data["confidence"]),
                "compliance_score": int(policy_data["compliance_score"]),
                "violations": policy_data.get("violations", []),
                "recommendations": policy_data.get("recommendations", []),
                "explanation": policy_data.get("explanation", ""),
                "rag_metadata": policy_data.get("rag_metadata", {}),
                "file_path": policy_data["file_path"],
                "file_size_bytes": policy_data["file_size_bytes"],
            }
            
            result = self.client.table("policies").insert(data).execute()
            
            if result.data:
                logger.info(f"✅ Created policy {data['id']} in database")
                return result.data[0]
            else:
                raise Exception("No data returned from insert")
                
        except Exception as e:
            logger.error(f"❌ Failed to create policy: {e}")
            raise
    
    async def get_policy(self, policy_id: str) -> Optional[Dict[str, Any]]:
        """
        Get policy by ID.
        
        Args:
            policy_id: Policy UUID
            
        Returns:
            Policy data or None if not found
        """
        try:
            result = self.client.table("policies").select("*").eq("id", policy_id).execute()
            
            if result.data and len(result.data) > 0:
                return result.data[0]
            return None
            
        except Exception as e:
            logger.error(f"❌ Failed to get policy {policy_id}: {e}")
            return None
    
    async def get_all_policies(self) -> List[Dict[str, Any]]:
        """
        Get all policies ordered by created date (newest first).
        
        Returns:
            List of policies
        """
        try:
            result = self.client.table("policies").select("*").order("created_at", desc=True).execute()
            return result.data if result.data else []
            
        except Exception as e:
            logger.error(f"❌ Failed to get all policies: {e}")
            return []
    
    async def update_policy(self, policy_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update policy fields.
        
        Args:
            policy_id: Policy UUID
            updates: Fields to update
            
        Returns:
            True if successful
        """
        try:
            result = self.client.table("policies").update(updates).eq("id", policy_id).execute()
            return bool(result.data)
            
        except Exception as e:
            logger.error(f"❌ Failed to update policy {policy_id}: {e}")
            return False
    
    async def delete_policy(self, policy_id: str) -> bool:
        """
        Delete policy (cascades to chat sessions/messages).
        
        Args:
            policy_id: Policy UUID
            
        Returns:
            True if successful
        """
        try:
            result = self.client.table("policies").delete().eq("id", policy_id).execute()
            logger.info(f"🗑️  Deleted policy {policy_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to delete policy {policy_id}: {e}")
            return False
    
    # ============= CHAT OPERATIONS =============
    
    async def get_or_create_chat_session(self, policy_id: str) -> str:
        """
        Get existing chat session or create new one.
        
        Args:
            policy_id: Policy UUID
            
        Returns:
            Session ID
        """
        try:
            # Try to get existing active session
            result = self.client.table("chat_sessions")\
                .select("id")\
                .eq("policy_id", policy_id)\
                .order("last_activity_at", desc=True)\
                .limit(1)\
                .execute()
            
            if result.data and len(result.data) > 0:
                session_id = result.data[0]["id"]
                logger.info(f"♻️  Reusing chat session {session_id}")
                return session_id
            
            # Create new session
            new_session = {
                "policy_id": policy_id,
                "message_count": 0
            }
            
            result = self.client.table("chat_sessions").insert(new_session).execute()
            
            if result.data:
                session_id = result.data[0]["id"]
                logger.info(f"✨ Created new chat session {session_id}")
                return session_id
            else:
                raise Exception("Failed to create chat session")
                
        except Exception as e:
            logger.error(f"❌ Failed to get/create chat session: {e}")
            raise
    
    async def add_chat_message(self, session_id: str, role: str, content: str) -> bool:
        """
        Add message to chat session.
        
        Args:
            session_id: Chat session UUID
            role: 'user' or 'assistant'
            content: Message content
            
        Returns:
            True if successful
        """
        try:
            # Validate content length
            if len(content) > 10000:
                content = content[:10000] + "... (truncated)"
            
            message_data = {
                "session_id": session_id,
                "role": role,
                "content": content
            }
            
            result = self.client.table("chat_messages").insert(message_data).execute()
            return bool(result.data)
            
        except Exception as e:
            logger.error(f"❌ Failed to add chat message: {e}")
            return False
    
    async def get_chat_history(self, session_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent chat messages for session.
        
        Args:
            session_id: Chat session UUID
            limit: Maximum messages to return (default 10)
            
        Returns:
            List of messages
        """
        try:
            result = self.client.table("chat_messages")\
                .select("role, content, created_at")\
                .eq("session_id", session_id)\
                .order("created_at", desc=True)\
                .limit(limit)\
                .execute()
            
            if result.data:
                # Reverse to get chronological order
                return list(reversed(result.data))
            return []
            
        except Exception as e:
            logger.error(f"❌ Failed to get chat history: {e}")
            return []
    
    async def cleanup_old_sessions(self) -> int:
        """
        Clean up chat sessions older than 7 days.
        
        Returns:
            Number of sessions deleted
        """
        try:
            # Call the database function
            result = self.client.rpc("cleanup_old_chat_sessions").execute()
            logger.info("🧹 Cleaned up old chat sessions")
            return 0  # Function doesn't return count, but that's OK
            
        except Exception as e:
            logger.error(f"❌ Failed to cleanup sessions: {e}")
            return 0
    
    # ============= STATISTICS =============
    
    async def get_statistics(self) -> Dict[str, Any]:
        """
        Get dashboard statistics with optimized database queries.
        Uses aggregation instead of fetching all policies.
        
        Returns:
            Statistics dictionary
        """
        try:
            # Get total count
            total_result = self.client.table("policies")\
                .select("*", count="exact")\
                .execute()
            total = total_result.count if hasattr(total_result, 'count') else len(total_result.data or [])
            
            if total == 0:
                return {
                    "totalPolicies": 0,
                    "compliantPolicies": 0,
                    "nonCompliantPolicies": 0,
                    "reviewRequired": 0,
                    "averageScore": 0,
                    "recentAnalyses": []
                }
            
            # Get counts by classification using separate queries
            compliant_result = self.client.table("policies")\
                .select("*", count="exact")\
                .eq("classification", "COMPLIANT")\
                .execute()
            compliant = compliant_result.count if hasattr(compliant_result, 'count') else len(compliant_result.data or [])
            
            non_compliant_result = self.client.table("policies")\
                .select("*", count="exact")\
                .eq("classification", "NON_COMPLIANT")\
                .execute()
            non_compliant = non_compliant_result.count if hasattr(non_compliant_result, 'count') else len(non_compliant_result.data or [])
            
            review_result = self.client.table("policies")\
                .select("*", count="exact")\
                .eq("classification", "REQUIRES_REVIEW")\
                .execute()
            review = review_result.count if hasattr(review_result, 'count') else len(review_result.data or [])
            
            # Get average score (need to fetch data for this)
            scores_result = self.client.table("policies")\
                .select("compliance_score")\
                .execute()
            
            if scores_result.data:
                total_score = sum(p["compliance_score"] for p in scores_result.data)
                avg_score = round(total_score / len(scores_result.data))
            else:
                avg_score = 0
            
            # Get recent 5 analyses
            recent_result = self.client.table("policies")\
                .select("id, filename, classification, compliance_score")\
                .order("created_at", desc=True)\
                .limit(5)\
                .execute()
            
            recent = recent_result.data or []
            
            logger.info(f"📊 Statistics: {total} policies, {compliant} compliant, {non_compliant} non-compliant, {review} review")
            
            return {
                "totalPolicies": total,
                "compliantPolicies": compliant,
                "nonCompliantPolicies": non_compliant,
                "reviewRequired": review,
                "averageScore": avg_score,
                "recentAnalyses": [
                    {
                        "id": p["id"],
                        "filename": p["filename"],
                        "classification": p["classification"],
                        "score": p["compliance_score"]
                    }
                    for p in recent
                ]
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to get statistics: {e}")
            return {
                "totalPolicies": 0,
                "compliantPolicies": 0,
                "nonCompliantPolicies": 0,
                "reviewRequired": 0,
                "averageScore": 0,
                "recentAnalyses": []
            }


# Global instance
_supabase_service: Optional[SupabaseService] = None


def get_supabase_service() -> SupabaseService:
    """Get or create Supabase service instance."""
    global _supabase_service
    if _supabase_service is None:
        _supabase_service = SupabaseService()
    return _supabase_service
