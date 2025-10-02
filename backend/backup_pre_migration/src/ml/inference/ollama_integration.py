import requests
import json
import logging
from typing import Dict, List, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class OllamaConfig:
    """Configuration for Ollama integration"""
    base_url: str = "http://localhost:11434"
    model: str = "llama3.1"
    timeout: int = 120
    temperature: float = 0.3
    max_tokens: int = 1000

class OllamaClient:
    """Client for interacting with Ollama API"""
    
    def __init__(self, config: OllamaConfig = None):
        self.config = config or OllamaConfig()
        self.base_url = self.config.base_url.rstrip('/')
        
    def is_available(self) -> bool:
        """Check if Ollama service is available"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False
    
    def list_models(self) -> List[str]:
        """List available models"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=10)
            if response.status_code == 200:
                data = response.json()
                return [model['name'] for model in data.get('models', [])]
        except requests.exceptions.RequestException as e:
            logger.error(f"Error listing models: {e}")
        return []
    
    def generate(self, prompt: str, system_prompt: str = None) -> Dict[str, any]:
        """Generate response from Ollama"""
        try:
            payload = {
                "model": self.config.model,
                "prompt": prompt,
                "options": {
                    "temperature": self.config.temperature,
                    "num_predict": self.config.max_tokens
                },
                "stream": False
            }
            
            if system_prompt:
                payload["system"] = system_prompt
            
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=self.config.timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "success": True,
                    "response": result.get("response", ""),
                    "model": result.get("model", ""),
                    "done": result.get("done", False),
                    "total_duration": result.get("total_duration", 0),
                    "eval_count": result.get("eval_count", 0)
                }
            else:
                logger.error(f"Ollama API error: {response.status_code} - {response.text}")
                return {"success": False, "error": f"API error: {response.status_code}"}
                
        except requests.exceptions.Timeout:
            logger.error("Ollama request timed out")
            return {"success": False, "error": "Request timed out"}
        except requests.exceptions.RequestException as e:
            logger.error(f"Ollama request error: {e}")
            return {"success": False, "error": str(e)}

class ComplianceExplainer:
    """Generates human-readable explanations for compliance decisions"""
    
    def __init__(self, ollama_client: OllamaClient):
        self.ollama_client = ollama_client
        
        # System prompt for compliance explanations
        self.system_prompt = """You are an expert in insurance regulations and compliance. 
        Your task is to provide clear, detailed explanations of compliance decisions based on IRDAI guidelines.
        Always be factual, specific, and cite relevant regulatory requirements when possible.
        Use professional language but make explanations understandable to non-experts."""
    
    def explain_classification(self, 
                             document_text: str, 
                             classification: str, 
                             confidence: float,
                             violations: List[Dict] = None,
                             context: Dict = None) -> str:
        """Generate explanation for compliance classification"""
        
        prompt = f"""
        Document Classification: {classification}
        Confidence Score: {confidence:.2f}

        Document Text (excerpt):
        {document_text[:2000]}...

        Please provide a detailed explanation of why this document was classified as '{classification}'.
        
        Consider the following aspects:
        1. What specific elements in the document led to this classification?
        2. Which IRDAI guidelines or regulations are relevant?
        3. What are the key compliance requirements that were or were not met?
        4. What actions should be taken based on this classification?

        If violations were found, explain them clearly.
        If the document is compliant, highlight the positive aspects.
        If review is required, explain what needs to be examined further.
        """
        
        if violations:
            prompt += f"\n\nIdentified Issues:\n"
            for i, violation in enumerate(violations, 1):
                prompt += f"{i}. {violation.get('description', 'Unknown issue')}\n"
        
        result = self.ollama_client.generate(prompt, self.system_prompt)
        
        if result.get("success"):
            return result["response"]
        else:
            return f"Unable to generate explanation: {result.get('error', 'Unknown error')}"
    
    def generate_recommendations(self,
                               document_text: str,
                               classification: str,
                               violations: List[Dict] = None) -> str:
        """Generate actionable recommendations"""
        
        prompt = f"""
        Based on the compliance analysis of this insurance document:
        
        Classification: {classification}
        
        Document excerpt:
        {document_text[:1500]}...
        
        Please provide specific, actionable recommendations for:
        1. Immediate steps to address any issues
        2. Long-term compliance improvements
        3. Risk mitigation strategies
        4. Next steps in the compliance process
        
        Make recommendations practical and specific to insurance industry practices.
        """
        
        if violations:
            prompt += f"\n\nSpecific issues to address:\n"
            for i, violation in enumerate(violations, 1):
                prompt += f"{i}. {violation.get('description', 'Issue description')}\n"
        
        result = self.ollama_client.generate(prompt, self.system_prompt)
        
        if result.get("success"):
            return result["response"]
        else:
            return f"Unable to generate recommendations: {result.get('error', 'Unknown error')}"
    
    def explain_violation(self, 
                         violation_text: str, 
                         regulation_reference: str = None) -> str:
        """Explain a specific compliance violation"""
        
        prompt = f"""
        Compliance Violation Detected:
        
        Violation Text: {violation_text}
        """
        
        if regulation_reference:
            prompt += f"Relevant Regulation: {regulation_reference}\n"
        
        prompt += """
        Please explain:
        1. What specific regulation or guideline is being violated?
        2. Why is this considered a violation?
        3. What are the potential consequences?
        4. How can this violation be corrected?
        5. What preventive measures can be implemented?
        
        Provide a clear, detailed explanation that would help someone understand and address this compliance issue.
        """
        
        result = self.ollama_client.generate(prompt, self.system_prompt)
        
        if result.get("success"):
            return result["response"]
        else:
            return f"Unable to explain violation: {result.get('error', 'Unknown error')}"
    
    def generate_compliance_summary(self, 
                                   document_results: List[Dict]) -> str:
        """Generate summary for batch compliance analysis"""
        
        total_docs = len(document_results)
        compliant = sum(1 for r in document_results if r.get('classification') == 'COMPLIANT')
        non_compliant = sum(1 for r in document_results if r.get('classification') == 'NON_COMPLIANT')
        needs_review = sum(1 for r in document_results if r.get('classification') == 'REQUIRES_REVIEW')
        
        prompt = f"""
        Compliance Analysis Summary:
        
        Total Documents Analyzed: {total_docs}
        Compliant: {compliant}
        Non-Compliant: {non_compliant}  
        Requires Review: {needs_review}
        
        Document Details:
        """
        
        for i, result in enumerate(document_results[:5], 1):  # Limit to first 5 for prompt size
            prompt += f"""
        {i}. Classification: {result.get('classification', 'Unknown')}
           Confidence: {result.get('confidence', 0):.2f}
           Key Issues: {', '.join(result.get('violations', [])[:3])}
        """
        
        prompt += """
        
        Please provide:
        1. Overall compliance status assessment
        2. Key trends and patterns in the violations
        3. Priority areas for immediate attention
        4. Strategic recommendations for improving compliance
        5. Risk assessment based on the findings
        
        Format the response as a professional compliance report summary.
        """
        
        result = self.ollama_client.generate(prompt, self.system_prompt)
        
        if result.get("success"):
            return result["response"]
        else:
            return f"Unable to generate summary: {result.get('error', 'Unknown error')}"

class ComplianceQA:
    """Question-answering system for compliance queries"""
    
    def __init__(self, ollama_client: OllamaClient):
        self.ollama_client = ollama_client
        self.system_prompt = """You are an expert consultant specializing in Indian insurance regulations and IRDAI guidelines.
        Provide accurate, detailed answers to compliance-related questions.
        Always cite specific regulations when possible and provide practical guidance."""
    
    def answer_question(self, question: str, context: str = None) -> str:
        """Answer compliance-related questions"""
        
        prompt = f"""
        Question: {question}
        """
        
        if context:
            prompt += f"\nContext: {context}\n"
        
        prompt += """
        Please provide a comprehensive answer that includes:
        1. Direct answer to the question
        2. Relevant IRDAI regulations or guidelines
        3. Practical implications
        4. Examples if applicable
        5. Any important caveats or exceptions
        """
        
        result = self.ollama_client.generate(prompt, self.system_prompt)
        
        if result.get("success"):
            return result["response"]
        else:
            return f"Unable to answer question: {result.get('error', 'Unknown error')}"