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
from ...dependencies import get_compliance_service

logger = get_logger(__name__)

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
    Chat with AI about a policy using RAG + LLaMA.
    
    Uses the full analysis context including violations, regulations,
    and compliance details to provide accurate, context-aware responses.
    
    Args:
        request: Chat request with message and session ID (policy_id)
        
    Returns:
        AI-generated response with full policy context
    """
    try:
        # Import policies store to get analysis results
        from .policies import policies_store
        
        # Get policy data - this contains the full analysis
        policy_data = policies_store.get(request.session_id)
        
        if not policy_data:
            return ChatResponse(
                response="I don't have analysis data for this policy. Please ensure the policy has been analyzed first.",
                session_id=request.session_id,
                timestamp=datetime.utcnow().isoformat()
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
        
        logger.info(f"Chat response generated for session {request.session_id}")
        
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


def _build_chat_context(message: str, policy_data: Optional[Dict[str, Any]]) -> str:
    """Build context string for LLaMA (legacy, for backward compatibility)."""
    if not policy_data:
        return f"""You are an AI compliance assistant specializing in IRDAI insurance regulations.
        
User Question: {message}

Please provide a helpful response about insurance compliance and IRDAI regulations."""
    
    context = f"""You are an AI compliance assistant. You have analyzed an insurance policy document.

Policy Information:
- Filename: {policy_data.get('filename', 'Unknown')}
- Classification: {policy_data.get('classification', 'Unknown')}
- Compliance Score: {policy_data.get('compliance_score', 0)}%
- Confidence: {policy_data.get('confidence', 0) * 100:.1f}%

Analysis Summary:
{policy_data.get('explanation', 'No explanation available')}

Violations Found: {len(policy_data.get('violations', []))}
"""
    
    if policy_data.get('violations'):
        context += "\nKey Violations:\n"
        for i, violation in enumerate(policy_data['violations'][:3], 1):
            context += f"{i}. [{violation.get('severity', 'UNKNOWN')}] {violation.get('description', 'No description')}\n"
    
    if policy_data.get('recommendations'):
        context += "\nRecommendations:\n"
        for i, rec in enumerate(policy_data['recommendations'][:3], 1):
            context += f"{i}. {rec}\n"
    
    context += f"\nUser Question: {message}\n"
    context += "\nProvide a clear, accurate response based on the policy analysis above."
    
    return context


async def _generate_fallback_response(
    message: str,
    policy_data: Optional[Dict[str, Any]]
) -> str:
    """Generate fallback response if LLaMA is unavailable."""
    
    message_lower = message.lower()
    
    # Question about violations
    if any(word in message_lower for word in ['violation', 'violate', 'issue', 'problem']):
        if not policy_data:
            return "I don't have information about a specific policy. Please upload a policy first to analyze violations."
        
        violations = policy_data.get('violations', [])
        if not violations:
            return "Great news! No violations were found in this policy. It appears to be compliant with IRDAI regulations."
        
        response = f"The analysis found {len(violations)} violation(s) in this policy:\n\n"
        for i, v in enumerate(violations[:5], 1):
            response += f"{i}. **{v.get('severity', 'UNKNOWN')} - {v.get('type', 'Unknown Type')}**\n"
            response += f"   {v.get('description', 'No description available')}\n"
            response += f"   Regulation: {v.get('regulation_reference', 'N/A')}\n\n"
        
        return response
    
    # Question about compliance
    if any(word in message_lower for word in ['compliant', 'compliance', 'status']):
        if not policy_data:
            return "Please upload a policy to check its compliance status."
        
        classification = policy_data.get('classification', 'UNKNOWN')
        score = policy_data.get('compliance_score', 0)
        
        return f"""This policy is classified as **{classification}** with a compliance score of **{score}%**.

{policy_data.get('explanation', 'No detailed explanation available.')}"""
    
    # Question about recommendations
    if any(word in message_lower for word in ['recommend', 'fix', 'improve', 'should']):
        if not policy_data:
            return "Upload a policy to get personalized recommendations."
        
        recommendations = policy_data.get('recommendations', [])
        if not recommendations:
            return "No specific recommendations needed. The policy appears to be in good standing."
        
        response = "Here are the recommended actions to improve compliance:\n\n"
        for i, rec in enumerate(recommendations, 1):
            response += f"{i}. {rec}\n"
        
        return response
    
    # Question about regulations
    if any(word in message_lower for word in ['regulation', 'irdai', 'rule', 'law']):
        if policy_data and policy_data.get('rag_metadata', {}).get('top_sources'):
            sources = policy_data['rag_metadata']['top_sources']
            response = f"This policy was analyzed against {len(sources)} IRDAI regulations:\n\n"
            for i, source in enumerate(sources[:5], 1):
                response += f"{i}. {source}\n"
            return response
        
        return """IRDAI (Insurance Regulatory and Development Authority of India) regulations govern insurance policies in India. 
The system analyzes policies against 203+ regulations including coverage requirements, disclosure norms, and customer protection guidelines."""
    
    # Default response
    if policy_data:
        return f"""I'm here to help you understand this policy analysis. The policy "{policy_data.get('filename', 'Unknown')}" 
has been classified as **{policy_data.get('classification', 'UNKNOWN')}** with a compliance score of **{policy_data.get('compliance_score', 0)}%**.

You can ask me about:
- Violations found
- Compliance status
- Recommendations for improvement
- IRDAI regulations applied
- Specific sections or concerns

What would you like to know?"""
    
    return """Hello! I'm your AI compliance assistant. I can help you understand:

- Policy compliance analysis
- IRDAI regulations
- Violations and how to fix them
- Compliance best practices

Please upload a policy to get started, or ask me a specific question about insurance compliance."""


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
