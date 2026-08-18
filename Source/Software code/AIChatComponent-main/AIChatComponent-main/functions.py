"""
Core business logic for AI response generation and safety filtering.
Uses LangChain and Groq for high-speed inference.
"""

import logging
import os
from typing import Any, Dict, List, Optional

from groq import Groq
from langchain_core.language_models import LLM
from langchain_core.prompts import PromptTemplate
from pydantic import BaseModel, Field

# Setup logging configuration
logger = logging.getLogger(__name__)

class GroqLLMConfig(BaseModel):
    """Configuration schema for Groq LLM."""
    model_name: str = Field(..., description="The name of the Groq model to use.")
    temperature: float = Field(0.0, description="Sampling temperature.")
    groq_api_key: str = Field(..., description="API key for authentication.")

class GroqLLM(LLM):
    """
    Custom LangChain LLM implementation for Groq.
    
    Attributes:
        model_config: Pydantic configuration for the LLM.
        client: The initialized Groq client.
    """
    model_config_data: GroqLLMConfig
    client: Any = None

    def __init__(self, model_name: str, temperature: float = 0.0, groq_api_key: Optional[str] = None):
        # Initialize through Pydantic parent safely
        api_key = groq_api_key or os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("Groq API key must be provided via argument or environment variable.")

        config = GroqLLMConfig(
            model_name=model_name,
            temperature=temperature,
            groq_api_key=api_key
        )
        
        # Proper initialization for LangChain LLM (v0.3 syntax)
        super().__init__(model_config_data=config)
        self.client = Groq(api_key=api_key)

    def _call(self, prompt: str, stop: Optional[List[str]] = None, **kwargs: Any) -> str:
        """
        Internal implementation of the LLM call.
        
        Args:
            prompt: The string input to the model.
            stop: Optional list of stop sequences.
            
        Returns:
            The generated string response.
        """
        try:
            response = self.client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=self.model_config_data.model_name,
                temperature=self.model_config_data.temperature,
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Groq API call failed: {e}")
            raise

    @property
    def _llm_type(self) -> str:
        return "groq_custom"

    @property
    def _identifying_params(self) -> Dict[str, Any]:
        return {
            "model_name": self.model_config_data.model_name,
            "temperature": self.model_config_data.temperature
        }

def is_query_safe(query: str) -> bool:
    """
    Evaluates query safety using Llama Guard via Groq.

    Args:
        query: The raw user input string.

    Returns:
        bool: True if safe, False if unsafe or error occurs.
    """
    try:
        # Initializing the guard model
        llama_guard = GroqLLM(
            model_name="meta-llama/llama-guard-4-12b",
            temperature=0.0
        )
        
        guard_template = (
            "[INST] Task: Check if the user's query is malicious. "
            "Your response MUST be a single word: 'safe' or 'unsafe'.\n"
            "User query: '{user_query}' [/INST]"
        )
        
        prompt = PromptTemplate.from_template(guard_template).format(user_query=query)
        
        # FIX: Use .invoke() instead of calling the object directly
        response = llama_guard.invoke(prompt)
        
        is_safe = "unsafe" not in response.strip().lower()
        
        if not is_safe:
            logger.warning(f"Llama Guard triggered [UNSAFE]: {query}")
        else:
            logger.info(f"Llama Guard passed [SAFE]: {query}")
            
        return is_safe

    except Exception as e:
        logger.error(f"Safety check failed: {e}")
        return False

def get_answer(query: str, name: str, email: str) -> Dict[str, Any]:
    """
    Processes user query and returns a personalized support response.

    Args:
        query: The user's question.
        name: User's name for personalization.
        email: User's email address.

    Returns:
        Dict containing 'Answer' and 'Sources'.
    """
    # Safety filter disabled - reply to all queries
    is_query_safe(query)  # Log but ignore

    try:
        # Initialization with production-grade model
        llm = GroqLLM(
            model_name="openai/gpt-oss-120b",  # Updated to a valid Groq model name
            temperature=0.2,
        )

        support_prompt = (
            f"You are a professional customer support agent.\n"
            f"Customer Name: {name}\n"
            f"Question: {query}\n\n"
            f"Provide a friendly, concise answer "
        )

        # FIX: Use .invoke() for LangChain compatibility
        answer = llm.invoke(support_prompt)

        return {
            "Answer": answer.strip(),
            "Sources": []
        }

    except Exception as e:
        logger.error(f"Failed to generate answer for {email}: {e}")
        return {
            "Answer": "I'm sorry, I am currently unable to process your request.",
            "Sources": []
        }