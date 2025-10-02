"""
Ollama client for generating AI explanations.
"""

import asyncio
import aiohttp
from typing import Optional, Dict, Any, List
import json

from ...core import get_logger, settings
from ...core.exceptions import ExternalServiceError

logger = get_logger(__name__)


class OllamaClient:
    """
    Async client for Ollama AI model interactions.
    
    Provides AI-generated explanations for compliance analysis results.
    """
    
    def __init__(self):
        """Initialize Ollama client."""
        self.base_url = settings.OLLAMA_BASE_URL
        self.model = settings.OLLAMA_MODEL
        self.timeout = settings.OLLAMA_TIMEOUT
        self._session = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        self._session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.timeout)
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self._session:
            await self._session.close()
    
    async def test_connection(self) -> bool:
        """Test connection to Ollama service."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/api/tags") as response:
                    if response.status == 200:
                        logger.info("Ollama connection successful")
                        return True
                    else:
                        logger.warning(f"Ollama service returned status {response.status}")
                        return False
        except Exception as e:
            logger.warning(f"Ollama connection failed: {e}")
            return False
    
    async def generate_explanation(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: float = 0.7
    ) -> Optional[str]:
        """
        Generate explanation using Ollama.
        
        Args:
            prompt: Input prompt for explanation
            max_tokens: Maximum tokens in response
            temperature: Randomness in generation (0.0 to 1.0)
            
        Returns:
            Generated explanation text or None if failed
        """
        try:
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "top_p": 0.9,
                    "top_k": 40
                }
            }
            
            if max_tokens:
                payload["options"]["num_predict"] = max_tokens
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/api/generate",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=self.timeout)
                ) as response:
                    
                    if response.status != 200:
                        logger.error(f"Ollama API returned status {response.status}")
                        return None
                    
                    result = await response.json()
                    explanation = result.get("response", "").strip()
                    
                    if explanation:
                        logger.debug("Successfully generated explanation")
                        return explanation
                    else:
                        logger.warning("Ollama returned empty response")
                        return None
                        
        except asyncio.TimeoutError:
            logger.error("Ollama request timed out")
            return None
        except Exception as e:
            logger.error(f"Failed to generate explanation: {e}")
            return None
    
    async def generate_streaming_explanation(
        self,
        prompt: str,
        callback=None
    ) -> str:
        """
        Generate explanation with streaming response.
        
        Args:
            prompt: Input prompt
            callback: Optional callback for streaming tokens
            
        Returns:
            Complete generated text
        """
        try:
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": True
            }
            
            full_response = ""
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/api/generate",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=self.timeout)
                ) as response:
                    
                    if response.status != 200:
                        raise ExternalServiceError(f"Ollama API error: {response.status}")
                    
                    async for line in response.content:
                        if line:
                            try:
                                chunk = json.loads(line.decode())
                                token = chunk.get("response", "")
                                full_response += token
                                
                                if callback:
                                    await callback(token)
                                    
                            except json.JSONDecodeError:
                                continue
            
            return full_response.strip()
            
        except Exception as e:
            logger.error(f"Streaming explanation failed: {e}")
            raise ExternalServiceError(
                "Failed to generate streaming explanation",
                error_code="OLLAMA_STREAMING_ERROR",
                details={"error": str(e)}
            )
    
    async def list_models(self) -> List[Dict[str, Any]]:
        """List available Ollama models."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/api/tags") as response:
                    if response.status == 200:
                        result = await response.json()
                        return result.get("models", [])
                    else:
                        logger.error(f"Failed to list models: {response.status}")
                        return []
        except Exception as e:
            logger.error(f"Error listing models: {e}")
            return []
    
    def is_available(self) -> bool:
        """Check if Ollama service is configured and available."""
        return bool(self.base_url and self.model)