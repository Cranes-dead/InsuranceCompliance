"""
Chat endpoints for AI-powered policy Q&A.
Integrates with LLaMA for conversational analysis.
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime

from app.core import get_logger
from app.services.compliance_service import ComplianceService
from app.db import get_supabase_service
from ...dependencies import get_compliance_service

logger = get_logger(__name__)

# Chat message length limit
MAX_MESSAGE_LENGTH = 10000  # 10K characters

# Rate limiting: Bounded in-memory store with cleanup (use Redis for production)
MAX_MESSAGES_PER_MINUTE = 10
MAX_TRACKED_SESSIONS = 10000  # Max sessions to track before cleanup
message_timestamps: Dict[str, list] = {}


def _get_rate_limit_timestamps(policy_id: str, now: datetime) -> list:
    """Get cleaned timestamps for a policy, with global eviction if store is too large."""
    # Global cleanup: evict oldest sessions if we exceed the max
    if len(message_timestamps) > MAX_TRACKED_SESSIONS:
        # Sort sessions by their most recent timestamp and keep only the newest half
        sorted_sessions = sorted(
            message_timestamps.items(),
            key=lambda item: max(item[1]) if item[1] else datetime.min,
            reverse=True
        )
        message_timestamps.clear()
        for sid, timestamps in sorted_sessions[:MAX_TRACKED_SESSIONS // 2]:
            message_timestamps[sid] = timestamps
    
    # Per-session cleanup: remove timestamps older than 1 minute
    if policy_id in message_timestamps:
        message_timestamps[policy_id] = [
            ts for ts in message_timestamps[policy_id]
            if (now - ts).total_seconds() < 60
        ]
    else:
        message_timestamps[policy_id] = []
    
    return message_timestamps[policy_id]

router = APIRouter()


class ChatRequest(BaseModel):
    """Chat request model."""
    session_id: str  # Can be policy_id
    message: str
    policy_context: Optional[Dict[str, Any]] = None


class ChatResponse(BaseModel):
    """Chat response model."""
    response: str
    session_id: str
    timestamp: str


@router.post("/chat", response_model=ChatResponse)
async def chat_with_policy(
    request: ChatRequest,
    compliance_service: ComplianceService = Depends(get_compliance_service)
):
    """
    Chat with AI about a policy using RAG + LLaMA with database persistence.
    
    Edge cases handled:
    - Message length validation (10K character limit)
    - Chat session management in database
    - Message history persistence
    - Policy context validation
    
    Args:
        request: Chat request with message and session ID (policy_id)
        
    Returns:
        AI-generated response with full policy context
    """
    db = get_supabase_service()
    
    try:
        # Rate limiting: Max messages per minute per policy
        now = datetime.utcnow()
        policy_id = request.session_id
        
        # Get cleaned timestamps (handles eviction + per-session cleanup)
        timestamps = _get_rate_limit_timestamps(policy_id, now)
        
        # Check rate limit
        if len(timestamps) >= MAX_MESSAGES_PER_MINUTE:
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded. Maximum {MAX_MESSAGES_PER_MINUTE} messages per minute."
            )
        
        # Add current timestamp
        message_timestamps[policy_id].append(now)
        
        # Validate message length
        if len(request.message) > MAX_MESSAGE_LENGTH:
            raise HTTPException(
                status_code=400,
                detail=f"Message exceeds maximum length of {MAX_MESSAGE_LENGTH} characters"
            )
        
        # Get policy data from database
        policy_data = await db.get_policy(request.session_id)
        
        if not policy_data:
            return ChatResponse(
                response="I don't have analysis data for this policy. Please ensure the policy has been analyzed first.",
                session_id=request.session_id,
                timestamp=datetime.utcnow().isoformat()
            )
        
        # Validate policy has complete analysis data
        if not policy_data.get('classification') or not policy_data.get('rag_metadata'):
            return ChatResponse(
                response="This policy hasn't been fully analyzed yet. Please wait for the analysis to complete before chatting.",
                session_id=request.session_id,
                timestamp=datetime.utcnow().isoformat()
            )
        
        # Get or create chat session
        chat_session_id = await db.get_or_create_chat_session(request.session_id)
        
        # Store user message
        await db.add_chat_message(
            session_id=chat_session_id,
            role="user",
            content=request.message
        )
        
        # Prepare analysis results for RAG+LLaMA chat
        analysis_results = {
            'classification': policy_data.get('classification'),
            'confidence': policy_data.get('confidence', 0),
            'compliance_score': policy_data.get('compliance_score', 0),
            'violations': policy_data.get('violations', []),
            'mandatory_compliance': policy_data.get('rag_metadata', {}).get('mandatory_compliance', []),
            'explanation': policy_data.get('explanation', ''),
            'recommendations': policy_data.get('recommendations', []),
            'rag_metadata': policy_data.get('rag_metadata', {})
        }
        
        logger.info(f"Chat request for policy {request.session_id}: {request.message[:100]}")
        
        # Use RAG+LLaMA service for context-aware chat
        try:
            # Check if RAG+LLaMA service is available
            if hasattr(compliance_service, 'rag_llama_service') and compliance_service.rag_llama_service:
                response_text = await compliance_service.rag_llama_service.chat_about_policy(
                    session_id=request.session_id,
                    user_query=request.message,
                    analysis_results=analysis_results,
                    policy_text=None  # Can add policy text retrieval if needed
                )
            else:
                # Fallback to building context manually
                response_text = await _generate_contextual_response(
                    request.message,
                    analysis_results
                )
        except Exception as llm_error:
            logger.warning(f"LLaMA generation failed, using fallback: {llm_error}")
            response_text = await _generate_contextual_response(
                request.message,
                analysis_results
            )
        
        logger.info(f"✅ Chat response generated for session {request.session_id}")
        
        # Store assistant response in database
        await db.add_chat_message(
            session_id=chat_session_id,
            role="assistant",
            content=response_text
        )
        
        return ChatResponse(
            response=response_text,
            session_id=request.session_id,
            timestamp=datetime.utcnow().isoformat()
        )
    
    except Exception as e:
        logger.error(f"Chat error for session {request.session_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Chat error: {str(e)}"
        )


async def _generate_contextual_response(
    message: str,
    analysis_results: Dict[str, Any]
) -> str:
    """Generate context-aware response based on analysis results."""
    
    message_lower = message.lower()
    violations = analysis_results.get('violations', [])
    classification = analysis_results.get('classification', 'UNKNOWN')
    score = analysis_results.get('compliance_score', 0)
    recommendations = analysis_results.get('recommendations', [])
    explanation = analysis_results.get('explanation', '')
    
    # Question about why policy was flagged
    if any(word in message_lower for word in ['why', 'flag', 'flagged', 'reason', 'classified']):
        response = f"Your policy was classified as **{classification}** with a compliance score of **{score}%**.\n\n"
        
        if classification == "NON_COMPLIANT":
            response += "**Reasons for Non-Compliance:**\n\n"
        elif classification == "REQUIRES_REVIEW":
            response += "**Reasons for Review Requirement:**\n\n"
        else:
            response += "**Analysis Summary:**\n\n"
        
        # Add explanation
        if explanation:
            response += f"{explanation}\n\n"
        
        # List violations
        if violations:
            response += f"**{len(violations)} Violation(s) Found:**\n\n"
            for i, v in enumerate(violations[:5], 1):
                severity = v.get('severity', 'UNKNOWN')
                vtype = v.get('type', 'Unknown Type')
                desc = v.get('description', 'No description')
                reg = v.get('regulation_reference', 'N/A')
                
                response += f"{i}. **[{severity}] {vtype}**\n"
                response += f"   - Issue: {desc}\n"
                response += f"   - Regulation: {reg}\n\n"
        
        # Add recommendations
        if recommendations:
            response += "**Recommended Actions:**\n\n"
            for i, rec in enumerate(recommendations[:3], 1):
                response += f"{i}. {rec}\n"
        
        return response
    
    # Question about violations
    if any(word in message_lower for word in ['violation', 'issue', 'problem', 'wrong']):
        if not violations:
            return "No violations were found in this policy. It meets IRDAI compliance requirements."
        
        response = f"**{len(violations)} Violation(s) Identified:**\n\n"
        for i, v in enumerate(violations, 1):
            response += f"**{i}. [{v.get('severity')}] {v.get('type')}**\n"
            response += f"   - **Issue:** {v.get('description')}\n"
            response += f"   - **Regulation:** {v.get('regulation_reference')}\n"
            if v.get('recommendation'):
                response += f"   - **Fix:** {v.get('recommendation')}\n"
            response += "\n"
        
        return response
    
    # Question about recommendations/fixes
    if any(word in message_lower for word in ['recommend', 'fix', 'improve', 'should', 'how to']):
        if not recommendations and not violations:
            return "Your policy appears to be compliant. No specific recommendations are needed at this time."
        
        response = "**Recommendations to Improve Compliance:**\n\n"
        
        if recommendations:
            for i, rec in enumerate(recommendations, 1):
                response += f"{i}. {rec}\n"
        
        if violations:
            response += "\n**Specific Fixes for Violations:**\n\n"
            for i, v in enumerate(violations[:5], 1):
                if v.get('recommendation'):
                    response += f"• **{v.get('type')}:** {v.get('recommendation')}\n"
        
        return response
    
    # Question about regulations
    if any(word in message_lower for word in ['regulation', 'irdai', 'rule', 'compliance']):
        rag_metadata = analysis_results.get('rag_metadata', {})
        sources = rag_metadata.get('top_regulation_sources', [])
        
        response = f"**Compliance Analysis Summary:**\n\n"
        response += f"- Classification: **{classification}**\n"
        response += f"- Compliance Score: **{score}%**\n"
        response += f"- Violations Found: **{len(violations)}**\n\n"
        
        if sources:
            response += f"**IRDAI Regulations Analyzed ({len(sources)}):**\n\n"
            for i, source in enumerate(sources[:10], 1):
                response += f"{i}. {source}\n"
        
        return response
    
    # Default - provide overview
    response = f"**Policy Analysis Overview:**\n\n"
    response += f"- **Classification:** {classification}\n"
    response += f"- **Compliance Score:** {score}%\n"
    response += f"- **Violations:** {len(violations)}\n"
    response += f"- **Recommendations:** {len(recommendations)}\n\n"
    
    if explanation:
        response += f"**Summary:**\n{explanation[:500]}...\n\n"
    
    response += "**Ask me about:**\n"
    response += "- Why this policy was flagged\n"
    response += "- Specific violations found\n"
    response += "- How to fix compliance issues\n"
    response += "- IRDAI regulations applied\n"
    
    return response


# NOTE: _build_chat_context() and _generate_fallback_response() were removed
# as dead code (DEAD-06). The active path uses _generate_contextual_response().



@router.post("/chat/session")
async def create_chat_session(policy_id: str):
    """
    Create a new chat session for a policy.
    
    Args:
        policy_id: Policy UUID
        
    Returns:
        Session information
    """
    try:
        return {
            "session_id": policy_id,
            "created_at": datetime.utcnow().isoformat(),
            "status": "active"
        }
    
    except Exception as e:
        logger.error(f"Error creating chat session: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error creating chat session: {str(e)}"
        )
