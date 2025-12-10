"""ChatGPT integration for script generation and optimization."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

try:
    from dotenv import load_dotenv  # type: ignore[import]
except ImportError:
    load_dotenv = None  # type: ignore[assignment]

try:
    from openai import OpenAI  # type: ignore[import]
except ImportError:
    OpenAI = None  # type: ignore[assignment]


class ChatGPTHelper:
    """Helper class for ChatGPT API integration."""

    def __init__(self, api_key: Optional[str] = None) -> None:
        """Initialize ChatGPT helper.
        
        Args:
            api_key: OpenAI API key. If not provided, will try to get from OPENAI_API_KEY env var or .env file.
        """
        # Load .env file from project root (2 levels up from this file)
        if load_dotenv is not None:
            env_path = Path(__file__).resolve().parents[1] / ".env"
            print(f"[ChatGPT] Looking for .env at: {env_path}")
            if env_path.exists():
                print(f"[ChatGPT] .env file found!")
                load_dotenv(dotenv_path=env_path)
            else:
                print(f"[ChatGPT] .env file not found at {env_path}")
        else:
            print("[ChatGPT] python-dotenv not installed, skipping .env file")
        
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        
        # Debug output
        if self.api_key:
            print(f"[ChatGPT] API key found (starts with: {self.api_key[:10]}...)")
        else:
            print("[ChatGPT] No API key found!")
        
        if OpenAI is None:
            print("[ChatGPT] openai package not installed!")
        else:
            print("[ChatGPT] openai package is installed")
        
        self.client = None
        if self.api_key and OpenAI is not None:
            try:
                self.client = OpenAI(api_key=self.api_key)
                print("[ChatGPT] OpenAI client initialized successfully!")
            except Exception as e:
                print(f"[ChatGPT] Failed to initialize OpenAI client: {e}")

    def is_available(self) -> bool:
        """Check if ChatGPT is available."""
        return self.client is not None and self.api_key is not None

    def generate_script(self, description: str, context: str = "") -> Optional[str]:
        """Generate a Python script based on description.
        
        Args:
            description: Description of what the script should do
            context: Additional context (e.g., available functions)
            
        Returns:
            Generated Python script or None if failed
        """
        if not self.is_available():
            return None

        system_prompt = """You are an expert Python developer specializing in HWP (한글) automation scripts.
Your task is to generate Python scripts that use the following functions to automate HWP document creation:
- insert_text(text: str): Insert text into the document
- insert_paragraph(): Insert a paragraph break
- insert_equation(latex: str, font_size_pt: float = 14.0): Insert LaTeX equations
- insert_hwpeqn(hwpeqn: str, font_size_pt: float = 12.0, eq_font_name: str = "HYhwpEQ"): Insert HWP equation format
- insert_image(image_path: str): Insert an image into the document

Generate ONLY the Python code without any explanations or markdown formatting.
The code should be clean, well-commented, and follow best practices."""

        user_message = f"""Generate a Python script for HWP automation with the following requirements:

{description}

{f'Additional context:{context}' if context else ''}

Remember to include helpful comments and make the code reusable."""

        try:
            print("[ChatGPT] Generating script...")
            # Combine system prompt and user message for gpt-5-nano
            full_prompt = f"{system_prompt}\n\n{user_message}"
            response = self.client.responses.create(  # type: ignore[union-attr]
                model="gpt-5-nano",
                input=full_prompt
            )
            generated = response.output_text
            print(f"[ChatGPT] Script generated successfully ({len(generated)} characters)")
            return generated
        except Exception as e:
            print(f"[ChatGPT] ERROR generating script: {type(e).__name__}: {e}")
            return None

    def optimize_script(self, script: str, feedback: str = "") -> Optional[str]:
        """Optimize an existing script based on feedback.
        
        Args:
            script: The script to optimize
            feedback: Optional feedback about what to improve
            
        Returns:
            Optimized Python script or None if failed
        """
        if not self.is_available():
            return None

        system_prompt = """You are an expert Python developer specializing in HWP automation scripts.
Your task is to optimize and improve Python scripts that automate HWP document creation.
Improve code quality, efficiency, readability, and error handling.
Generate ONLY the optimized Python code without any explanations or markdown formatting."""

        user_message = f"""Please optimize this HWP automation script:

```python
{script}
```

{f'Optimization goals: {feedback}' if feedback else 'Focus on code quality, readability, and best practices.'}

Return only the optimized code without any explanations."""

        try:
            print("[ChatGPT] Optimizing script...")
            # Combine system prompt and user message for gpt-5-nano
            full_prompt = f"{system_prompt}\n\n{user_message}"
            response = self.client.responses.create(  # type: ignore[union-attr]
                model="gpt-5-nano",
                input=full_prompt
            )
            optimized = response.output_text
            print(f"[ChatGPT] Script optimized successfully ({len(optimized)} characters)")
            return optimized
        except Exception as e:
            print(f"[ChatGPT] ERROR optimizing script: {type(e).__name__}: {e}")
            return None

    def explain_script(self, script: str) -> Optional[str]:
        """Explain what a script does.
        
        Args:
            script: The script to explain
            
        Returns:
            Explanation of the script or None if failed
        """
        if not self.is_available():
            return None

        system_prompt = """You are an expert in explaining Python code for HWP automation.
Provide clear, concise explanations of what scripts do."""

        user_message = f"""Please explain what this HWP automation script does:

```python
{script}
```

Provide a clear, concise explanation of its purpose and what it accomplishes."""

        try:
            # Combine system prompt and user message for gpt-5-nano
            full_prompt = f"{system_prompt}\n\n{user_message}"
            response = self.client.responses.create(  # type: ignore[union-attr]
                model="gpt-5-nano",
                input=full_prompt
            )
            return response.output_text
        except Exception as e:
            print(f"[ChatGPT] ERROR explaining script: {type(e).__name__}: {e}")
            return None
