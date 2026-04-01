# src/agents/base_agent.py
import logging
import json
import os
import time
from typing import Dict, Optional
from openai import OpenAI
from langsmith.wrappers import wrap_openai
from dotenv import load_dotenv
from pathlib import Path
from src.utils.path import get_project_root


logging.basicConfig(level=logging.INFO)
# Load environment variables
load_dotenv()

class BaseAgent:
    """
    Base agent class with LangSmith integration for tracing
    
    Features:
    - OpenAI API integration
    - LangSmith tracing for observability
    - JSON response parsing
    - Error handling
    """
    
    def __init__(self, name: str, model: str = "gpt-4o-mini"):
        """
        Initialize base agent
        
        Args:
            name: Agent name (e.g., "WebAgent", "MobileAgent")
            model: OpenAI model to use (default: gpt-4o-mini)
        """
        self.name = name
        self.model = model
        # Get absolute path to THIS file
        self.agent_dir = Path(__file__).parent
        
        # Navigate to project root
        self.project_root = self.agent_dir.parent.parent
        
        # Build prompts directory
        self.prompts_dir = self.project_root / "src" / "prompts"
        
        # Initialize OpenAI client
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("❌ OPENAI_API_KEY not found in .env file!")
        
        # Create OpenAI client
        self.client = OpenAI(api_key=api_key)
        
        # Wrap with LangSmith for tracing
        self.client = wrap_openai(self.client)
        
        print(f"✅ {name} initialized with OpenAI ({model}) and LangSmith tracing")
    
    def call_llm(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> Dict:
        """
        Call OpenAI LLM with LangSmith tracing
        
        Args:
            system_prompt: System instruction for the LLM
            user_prompt: User message/question
            temperature: LLM temperature (0.0-2.0)
            max_tokens: Maximum tokens in response
        
        Returns:
            Dictionary with parsed JSON response or error
        """
        start_time = time.time()
        
        try:
            # Prepare messages
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ]
            
            # Call OpenAI API (automatically traced by LangSmith)
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,  # type: ignore
                temperature=temperature,
                max_tokens=max_tokens,
            )
            
            # Extract response text
            text_content = response.choices[0].message.content
            
            # Parse JSON response
            result = self._parse_json_response(text_content)
            
            # Calculate latency
            latency_ms = int((time.time() - start_time) * 1000)
            result["latency_ms"] = latency_ms
            
            return result
            
        except json.JSONDecodeError as e:
            latency_ms = int((time.time() - start_time) * 1000)
            error = {
                "error": "Invalid JSON response",
                "json_error": str(e),
                "latency_ms": latency_ms
            }
            print(f"❌ {self.name} JSON Parse Error: {e}")
            return error
        
        except Exception as e:
            latency_ms = int((time.time() - start_time) * 1000)
            error = {
                "error": str(e),
                "error_type": type(e).__name__,
                "latency_ms": latency_ms
            }
            print(f"❌ {self.name} Error: {e}")
            import traceback
            traceback.print_exc()
            return error
    
    def _parse_json_response(self, text_content: str) -> Dict:
        """
        Parse JSON from LLM response, handling markdown code blocks
        
        Args:
            text_content: Raw response text from LLM
        
        Returns:
            Parsed JSON as dictionary
        """
        json_str = text_content.strip()
        
        # Handle markdown code blocks (```json ... ```)
        if json_str.startswith("```"):
            parts = json_str.split("```")
            if len(parts) >= 2:
                json_str = parts[1]
                # Remove 'json' language identifier if present
                if json_str.startswith("json"):
                    json_str = json_str[4:]
        
        # Clean whitespace
        json_str = json_str.strip()
        
        # Parse JSON
        result = json.loads(json_str)
        
        return result
    
    def log_trace(self, agent_name: str, inputs: Dict, outputs: Dict, latency_ms: int) -> None:
        """
        Log trace information (LangSmith handles most of this automatically)
        
        Args:
            agent_name: Name of the agent
            inputs: Input data
            outputs: Output data
            latency_ms: Latency in milliseconds
        """
        print(f"[{agent_name}] ✓ Completed in {latency_ms}ms")

    def get_prompt_from_file(self, filename: str) -> str:

        """Utility to load prompt templates from files"""
        file_path = self.prompts_dir / filename
        try:
            with open(file_path, "r") as f:
                return f.read()
        except Exception as e:
            logging.error(f"❌ Error loading prompt from {filename}: {e}")
            return ""


