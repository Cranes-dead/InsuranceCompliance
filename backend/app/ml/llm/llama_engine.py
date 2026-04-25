"""LLaMA-based compliance reasoning engine.

This module provides interfaces to LLaMA for:
1. Compliance classification with reasoning
2. Conversational Q&A about policies
3. Section-level analysis

Supports both local (Ollama) and API-based (Groq, Together.ai) deployment.
"""

import json
import logging
from typing import Dict, List, Optional, Any, Literal
from abc import ABC, abstractmethod
import httpx
from pydantic import BaseModel, Field

from app.core.config import settings
from .prompt_templates import PromptTemplates

logger = logging.getLogger(__name__)


class LLMConfig(BaseModel):
    """Configuration for LLM provider."""
    provider: Literal["ollama", "groq", "together", "openai"] = "ollama"
    model: str = "llama3.1:8b"
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    temperature: float = 0.1  # Low temperature for consistent compliance analysis
    timeout: float = 300.0  # 5 minutes for complex compliance analysis
    max_tokens: int = 2048


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""
    
    @abstractmethod
    async def generate(self, prompt: str, temperature: float = 0.1) -> str:
        """Generate text from prompt."""
        pass


class OllamaProvider(LLMProvider):
    """Local Ollama provider."""
    
    def __init__(self, config: LLMConfig):
        self.config = config
        self.base_url = config.base_url or "http://localhost:11434"
        self.model = config.model
        self._client: Optional[httpx.AsyncClient] = None
    
    def _get_client(self) -> httpx.AsyncClient:
        """Get or create the persistent HTTP client."""
        if self._client is None or self._client.is_closed:
            timeout = httpx.Timeout(
                self.config.timeout,
                connect=60.0,
                read=self.config.timeout,
                write=30.0
            )
            self._client = httpx.AsyncClient(timeout=timeout)
        return self._client
        
    async def generate(self, prompt: str, temperature: float = 0.1) -> str:
        """Generate using Ollama API."""
        url = f"{self.base_url}/api/generate"
        client = self._get_client()
        
        try:
            response = await client.post(
                url,
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "temperature": temperature,
                    "stream": False
                }
            )
            response.raise_for_status()
            result = response.json()
            return result.get("response", "")
            
        except httpx.ConnectError:
            raise RuntimeError(
                f"Cannot connect to Ollama at {self.base_url}. "
                "Make sure Ollama is running (ollama serve)"
            )
        except Exception as e:
            logger.error(f"Ollama generation failed: {e}")
            raise
    
    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()


class GroqProvider(LLMProvider):
    """Groq API provider (fast inference)."""
    
    def __init__(self, config: LLMConfig):
        self.config = config
        self.api_key = config.api_key or settings.GROQ_API_KEY
        self.model = config.model or "llama-3.1-70b-versatile"
        self._client: Optional[httpx.AsyncClient] = None
        
        if not self.api_key:
            raise ValueError("Groq API key not configured")
    
    def _get_client(self) -> httpx.AsyncClient:
        """Get or create the persistent HTTP client."""
        if self._client is None or self._client.is_closed:
            timeout = httpx.Timeout(
                self.config.timeout,
                connect=30.0,
                read=self.config.timeout,
                write=30.0
            )
            self._client = httpx.AsyncClient(
                timeout=timeout,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
            )
        return self._client
    
    async def generate(self, prompt: str, temperature: float = 0.1) -> str:
        """Generate using Groq API."""
        url = "https://api.groq.com/openai/v1/chat/completions"
        client = self._get_client()
        
        try:
            payload = {
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": temperature,
                "max_tokens": self.config.max_tokens
            }
            
            response = await client.post(url, json=payload)
            
            # Log error details for debugging
            if response.status_code != 200:
                error_detail = response.text
                logger.error(f"Groq API error ({response.status_code}): {error_detail}")
            
            response.raise_for_status()
            result = response.json()
            return result["choices"][0]["message"]["content"]
            
        except Exception as e:
            logger.error(f"Groq generation failed: {e}")
            raise
    
    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()



class LLaMAComplianceEngine:
    """Main engine for LLaMA-based compliance reasoning."""
    
    def __init__(self, config: Optional[LLMConfig] = None):
        """Initialize the engine with provider configuration.
        
        Args:
            config: LLM configuration (defaults to local Ollama)
        """
        self.config = config or LLMConfig()
        self.provider = self._create_provider()
        self.templates = PromptTemplates()
        self._initialized = False
        
    def _create_provider(self) -> LLMProvider:
        """Create appropriate provider based on config."""
        if self.config.provider == "ollama":
            return OllamaProvider(self.config)
        elif self.config.provider == "groq":
            return GroqProvider(self.config)
        else:
            raise ValueError(f"Unsupported provider: {self.config.provider}")
    
    async def initialize(self) -> None:
        """Initialize and test the LLM connection."""
        if self._initialized:
            return
        
        try:
            logger.info(f"🤖 Testing {self.config.provider} connection...")
            test_prompt = "Reply with OK if you can read this."
            response = await self.provider.generate(test_prompt, temperature=0.0)
            
            if response:
                logger.info(f"✅ {self.config.provider} connected successfully")
                self._initialized = True
            else:
                raise RuntimeError("Empty response from LLM")
                
        except Exception as e:
            logger.error(f"❌ Failed to initialize LLM: {e}")
            raise
    
    async def _parse_json_response(self, response: str) -> Optional[Dict[str, Any]]:
        """Attempt to parse a JSON response from the LLM.
        
        Handles common LLM output patterns like markdown code blocks.
        Returns None if parsing fails (caller should handle retry/fallback).
        """
        try:
            json_str = response.strip()
            
            # Handle markdown code blocks
            if "```json" in json_str:
                json_str = json_str.split("```json")[1].split("```")[0].strip()
            elif "```" in json_str:
                json_str = json_str.split("```")[1].split("```")[0].strip()
            
            return json.loads(json_str)
            
        except (json.JSONDecodeError, IndexError, ValueError) as e:
            logger.debug(f"JSON parse failed: {e}. Raw (first 300 chars): {response[:300]}")
            return None
    
    async def analyze_compliance(
        self,
        policy_text: str,
        regulations: str,
        policy_metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Perform compliance analysis with reasoning.
        
        Args:
            policy_text: Full or summarized policy text
            regulations: Retrieved relevant regulations (formatted)
            policy_metadata: Optional policy metadata
            
        Returns:
            Structured analysis results
        """
        if not self._initialized:
            await self.initialize()
        
        # Generate prompt
        prompt = self.templates.classification_prompt(
            policy_text=policy_text,
            regulations=regulations,
            policy_metadata=policy_metadata
        )
        
        logger.info("🔍 Running LLaMA compliance analysis...")
        
        # Generate response
        response = await self.provider.generate(
            prompt,
            temperature=self.config.temperature
        )
        
        # Parse JSON response
        result = await self._parse_json_response(response)
        
        if result is not None:
            # Post-process: Ensure recommendations are strings (LLaMA sometimes returns dicts)
            if "recommendations" in result and isinstance(result["recommendations"], list):
                processed_recommendations = []
                for rec in result["recommendations"]:
                    if isinstance(rec, dict):
                        # Extract description field if it's a dict
                        processed_recommendations.append(rec.get("description", str(rec)))
                    else:
                        processed_recommendations.append(str(rec))
                result["recommendations"] = processed_recommendations
            
            logger.info(f"✅ Analysis complete: {result.get('classification')}")
            return result
        
        # LOGIC-03 FIX: Retry with a JSON repair prompt instead of silently returning 0%
        logger.warning("First JSON parse failed, attempting repair prompt...")
        repair_prompt = (
            "Your previous response was not valid JSON. Please fix it.\n"
            "Return ONLY a valid JSON object with these fields:\n"
            "- classification: one of COMPLIANT, NON_COMPLIANT, REQUIRES_REVIEW\n"
            "- confidence: float between 0 and 1\n"
            "- compliance_score: float between 0 and 100\n"
            "- explanation: string\n"
            "- violations: array of objects\n"
            "- recommendations: array of strings\n\n"
            f"Your original (broken) response was:\n{response[:1500]}\n\n"
            "Return ONLY the corrected JSON, no markdown, no explanation."
        )
        
        try:
            retry_response = await self.provider.generate(repair_prompt, temperature=0.0)
            retry_result = await self._parse_json_response(retry_response)
            
            if retry_result is not None:
                logger.info(f"✅ Repair prompt succeeded: {retry_result.get('classification')}")
                return retry_result
        except Exception as retry_err:
            logger.warning(f"Repair prompt also failed: {retry_err}")
        
        # Final fallback with visible error indication
        logger.error("Both original and repair JSON parsing failed")
        return {
            "classification": "REQUIRES_REVIEW",
            "confidence": 0.3,
            "compliance_score": 0.0,
            "explanation": "LLM analysis completed but response could not be parsed as structured JSON after retry.",
            "violations": [],
            "mandatory_compliance": [],
            "recommendations": ["Review the policy manually - automated analysis was inconclusive"],
            "parse_error": True,
            "raw_excerpt": response[:300]
        }
    
    async def chat(
        self,
        user_query: str,
        analysis_results: Dict[str, Any],
        chat_history: Optional[List[Dict[str, str]]] = None,
        policy_excerpt: str = ""
    ) -> str:
        """Handle conversational Q&A about compliance analysis.
        
        Args:
            user_query: User's question
            analysis_results: Previous analysis results
            chat_history: Previous conversation messages
            policy_excerpt: Optional relevant policy text
            
        Returns:
            Assistant's response
        """
        if not self._initialized:
            await self.initialize()
        
        chat_history = chat_history or []
        
        prompt = self.templates.chat_prompt(
            user_query=user_query,
            analysis_results=analysis_results,
            chat_history=chat_history,
            policy_excerpt=policy_excerpt
        )
        
        logger.info(f"💬 Processing user query: {user_query[:100]}...")
        
        response = await self.provider.generate(
            prompt,
            temperature=0.3  # Slightly higher for more natural conversation
        )
        
        return response.strip()
    
    async def analyze_section(
        self,
        section_text: str,
        section_type: str,
        regulations: str
    ) -> Dict[str, Any]:
        """Analyze a specific policy section.
        
        Args:
            section_text: Text of the policy section
            section_type: Type of section (coverage, exclusions, etc.)
            regulations: Relevant regulations
            
        Returns:
            Section analysis results
        """
        if not self._initialized:
            await self.initialize()
        
        prompt = self.templates.section_analysis_prompt(
            section_text=section_text,
            section_type=section_type,
            regulations=regulations
        )
        
        response = await self.provider.generate(prompt)
        
        try:
            json_str = response.strip()
            if "```json" in json_str:
                json_str = json_str.split("```json")[1].split("```")[0].strip()
            
            return json.loads(json_str)
        except (json.JSONDecodeError, ValueError, IndexError) as e:
            logger.warning(f"Failed to parse section analysis JSON: {e}")
            return {
                "section_compliant": None,
                "issues": [response],
                "missing_elements": [],
                "recommendations": []
            }
    
    async def close(self) -> None:
        """Close the provider's HTTP client for clean shutdown."""
        if hasattr(self.provider, 'close'):
            await self.provider.close()
    
    def get_info(self) -> Dict[str, Any]:
        """Get information about the engine configuration."""
        return {
            "provider": self.config.provider,
            "model": self.config.model,
            "base_url": self.config.base_url,
            "temperature": self.config.temperature,
            "initialized": self._initialized
        }
