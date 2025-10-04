"""Prompt templates for LLaMA compliance reasoning."""

from typing import List, Dict, Any


class PromptTemplates:
    """Centralized prompt templates for LLaMA interactions."""
    
    @staticmethod
    def classification_prompt(
        policy_text: str,
        regulations: str,
        policy_metadata: Dict[str, Any] = None
    ) -> str:
        """Generate prompt for compliance classification task.
        
        Args:
            policy_text: Full or summarized policy text
            regulations: Retrieved relevant regulations (formatted)
            policy_metadata: Optional metadata (file name, type, etc.)
            
        Returns:
            Formatted prompt string
        """
        metadata_section = ""
        if policy_metadata:
            metadata_section = f"""
POLICY METADATA:
- Document Name: {policy_metadata.get('filename', 'Unknown')}
- Document Type: {policy_metadata.get('type', 'Insurance Policy')}
- Analysis Date: {policy_metadata.get('date', 'Not specified')}
"""
        
        return f"""You are an expert insurance compliance analyst specializing in Indian motor vehicle insurance regulations. Your task is to analyze insurance policies for compliance with regulatory requirements set by IRDAI and MoRTH.

{metadata_section}

POLICY TEXT:
{policy_text[:4000]}  

RELEVANT REGULATIONS:
{regulations}

ANALYSIS TASK:
Analyze this policy against the regulations. Check:
1. Coverage Requirements - Are all mandatory coverages included with proper limits?
2. Exclusions - Are there any invalid exclusions or violations?
3. Terms & Conditions - Are clauses clear and regulatory-compliant?

CLASSIFICATION:
- COMPLIANT: Fully meets regulations
- NON_COMPLIANT: Clear violations exist
- REQUIRES_REVIEW: Ambiguous or needs human review

OUTPUT FORMAT (JSON):
{{
    "classification": "COMPLIANT|NON_COMPLIANT|REQUIRES_REVIEW",
    "confidence": 0.0-1.0,
    "compliance_score": 0.0-100.0,
    "violations": [
        {{
            "severity": "CRITICAL|HIGH|MEDIUM|LOW",
            "type": "MISSING_COVERAGE|INVALID_EXCLUSION|INADEQUATE_LIMITS|MISLEADING_TERMS|PRICING_VIOLATION",
            "description": "Clear description of the violation",
            "regulation_reference": "Specific regulation violated",
            "recommendation": "How to fix this violation"
        }}
    ],
    "mandatory_compliance": [
        {{
            "requirement": "Description of requirement",
            "status": "MET|NOT_MET|UNCLEAR",
            "evidence": "Quote from policy showing compliance/non-compliance"
        }}
    ],
    "explanation": "Detailed explanation of the classification decision with specific examples and regulation citations",
    "recommendations": [
        "Specific actionable recommendations for compliance"
    ]
}}

Provide your analysis in valid JSON format only. Be thorough, cite specific regulations, and provide clear evidence for your conclusions."""

    @staticmethod
    def chat_prompt(
        user_query: str,
        analysis_results: Dict[str, Any],
        chat_history: List[Dict[str, str]],
        policy_excerpt: str = ""
    ) -> str:
        """Generate prompt for conversational Q&A about analysis.
        
        Args:
            user_query: User's question
            analysis_results: Previous compliance analysis results
            chat_history: List of previous messages
            policy_excerpt: Optional relevant policy excerpt
            
        Returns:
            Formatted prompt string
        """
        # Format chat history
        history_text = ""
        if chat_history:
            history_text = "CONVERSATION HISTORY:\n"
            for msg in chat_history[-5:]:  # Last 5 messages for context
                role = msg.get('role', 'user')
                content = msg.get('content', '')
                history_text += f"{role.upper()}: {content}\n"
            history_text += "\n"
        
        # Format analysis results
        classification = analysis_results.get('classification', 'UNKNOWN')
        confidence = analysis_results.get('confidence', 0.0)
        violations = analysis_results.get('violations', [])
        explanation = analysis_results.get('explanation', 'No analysis available')
        
        violations_text = ""
        if violations:
            violations_text = "KEY VIOLATIONS FOUND:\n"
            for i, v in enumerate(violations[:5], 1):  # Top 5 violations
                violations_text += f"{i}. [{v.get('severity')}] {v.get('description')}\n"
            violations_text += "\n"
        
        policy_section = ""
        if policy_excerpt:
            policy_section = f"""
RELEVANT POLICY EXCERPT:
{policy_excerpt}
"""
        
        return f"""You are an expert insurance compliance advisor helping users understand policy compliance analysis results.

PREVIOUS ANALYSIS RESULTS:
- Classification: {classification}
- Confidence: {confidence:.1%}

{violations_text}

ANALYSIS EXPLANATION:
{explanation}

{history_text}{policy_section}

USER QUESTION:
{user_query}

Provide a clear, helpful answer that:
1. Directly addresses the user's question
2. References specific findings from the analysis
3. Cites relevant regulations when appropriate
4. Offers practical guidance or next steps
5. Uses plain language suitable for non-experts

Keep your response concise but thorough. If you reference a violation or requirement, explain it clearly."""

    @staticmethod
    def section_analysis_prompt(
        section_text: str,
        section_type: str,
        regulations: str
    ) -> str:
        """Generate prompt for analyzing a specific policy section.
        
        Args:
            section_text: Text of the policy section
            section_type: Type of section (coverage, exclusions, etc.)
            regulations: Relevant regulations for this section
            
        Returns:
            Formatted prompt string
        """
        return f"""Analyze this specific section of an insurance policy for compliance.

SECTION TYPE: {section_type.upper()}

SECTION TEXT:
{section_text}

RELEVANT REGULATIONS:
{regulations}

Provide a focused analysis of this section, identifying:
1. Whether this section meets regulatory requirements
2. Any specific violations or concerns
3. Missing required elements
4. Ambiguous or problematic language

Output as JSON with structure:
{{
    "section_compliant": true/false,
    "issues": ["list of specific issues"],
    "missing_elements": ["required elements not found"],
    "recommendations": ["specific improvements needed"]
}}"""

    @staticmethod
    def summarization_prompt(policy_text: str, max_length: int = 1000) -> str:
        """Generate prompt for policy summarization (for long documents).
        
        Args:
            policy_text: Full policy text
            max_length: Target summary length in words
            
        Returns:
            Formatted prompt string
        """
        return f"""Summarize this insurance policy document, focusing on key compliance-relevant information:

POLICY TEXT:
{policy_text[:8000]}

Create a concise summary (around {max_length} words) that captures:
1. Type of coverage provided
2. Coverage limits and key benefits
3. Important exclusions
4. Special terms or conditions
5. Premium and payment details
6. Any unusual or noteworthy clauses

Focus on information relevant to regulatory compliance analysis."""
