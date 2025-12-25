"""ChatGPT integration for script generation and optimization."""

from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Optional, Callable

try:
    from dotenv import load_dotenv  # type: ignore[import]
except ImportError:
    load_dotenv = None  # type: ignore[assignment]

try:
    from openai import OpenAI, RateLimitError  # type: ignore[import]
except ImportError:
    OpenAI = None  # type: ignore[assignment]
    RateLimitError = None  # type: ignore[assignment]


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

    def _call_api_with_retry(self, full_prompt: str, model: str = "gpt-5-nano", max_retries: int = 3) -> Optional[str]:
        """Call OpenAI API with retry logic for rate limits.
        
        Args:
            full_prompt: The full prompt to send to the API
            model: The model to use
            max_retries: Maximum number of retries on rate limit
            
        Returns:
            API response text or None if failed
        """
        if not self.client:
            print("[ChatGPT] ERROR: No client available")
            return None
        
        for attempt in range(max_retries):
            try:
                print(f"[ChatGPT] API call attempt {attempt + 1}/{max_retries}...")
                response = self.client.responses.create(  # type: ignore[union-attr]
                    model=model,
                    input=full_prompt
                )
                
                # Check if response has output_text
                if hasattr(response, 'output_text'):
                    result = response.output_text
                    if result:
                        print(f"[ChatGPT] API returned {len(result)} characters")
                        return result
                    else:
                        print("[ChatGPT] WARNING: API returned empty output_text")
                        return None
                else:
                    print(f"[ChatGPT] WARNING: Response object has no output_text attribute. Response type: {type(response)}")
                    print(f"[ChatGPT] Response attributes: {dir(response)}")
                    return None
                    
            except Exception as e:
                error_name = type(e).__name__
                error_msg = str(e)
                print(f"[ChatGPT] Exception on attempt {attempt + 1}: {error_name}: {error_msg}")
                
                # Check for rate limit error
                if "RateLimitError" in error_name or "rate" in error_msg.lower():
                    if attempt < max_retries - 1:
                        wait_time = (2 ** attempt) + 1  # Exponential backoff: 2, 5, 10 seconds
                        print(f"[ChatGPT] Rate limit hit. Waiting {wait_time}s before retry {attempt + 1}/{max_retries}...")
                        time.sleep(wait_time)
                        continue
                    else:
                        print(f"[ChatGPT] Max retries reached for rate limit")
                        return None
                else:
                    print(f"[ChatGPT] Non-rate-limit error, not retrying: {error_name}: {error_msg}")
                    return None
        
        print("[ChatGPT] All retry attempts exhausted")
        return None

    def generate_script(self, description: str, context: str = "", on_thought: Optional[Callable[[str], None]] = None) -> Optional[str]:
        """Generate a Python script based on description.
        
        Args:
            description: Description of what the script should do
            context: Additional context (e.g., available functions)
            on_thought: Optional callback function to receive thought process updates
            
        Returns:
            Generated Python script or None if failed
        """
        if not self.is_available():
            return None

        system_prompt = (
            "You are an expert Python developer specializing in HWP (한글) automation scripts. "
            "Your task is to generate only the minimal Python code needed for the user's request, using the following functions: "
            "- insert_text(text: str): Insert text into the document (텍스트) "
            "- insert_paragraph(): Insert a paragraph break "
            "- insert_equation(latex: str, font_size_pt: float = 14.0): Insert LaTeX equations (벡터, 행렬, 시그마, 미분, 적분 등) "
            "- insert_hwpeqn(hwpeqn: str, font_size_pt: float = 12.0, eq_font_name: str = 'HYhwpEQ'): Insert HWP equation format "
            "- insert_image(image_path: str): Insert an image into the document "
            "- insert_table(rows: int, cols: int, treat_as_char: bool = False, cell_data: list = None): Insert a table/chart (표). "
            "  Example with data: insert_table(rows=3, cols=2, cell_data=[['Header1', 'Header2'], ['Data1', 'Data2'], ['Data3', 'Data4']]) "
            "When user asks for 벡터 (vector), 행렬 (matrix), 시그마 (summation), 미분 (derivative), 적분 (integral), or 표 (table), "
            "use the appropriate function to insert that mathematical or structural element. "
            "\n\nLaTeX Reference Guide:\n"
            "Basic Formulas: x = \\frac{-b \\pm \\sqrt{b^2-4ac}}{2a}, E = mc^2\n"
            "Integrals: \\int_{0}^{\\infty} e^{-x^2} dx, \\int x^n dx = \\frac{x^{n+1}}{n+1}\n"
            "Sum & Product: \\sum_{i=1}^{n} i = \\frac{n(n+1)}{2}, \\prod_{i=1}^{n} a_i\n"
            "Fractions & Roots: \\frac{a}{b}, \\sqrt{x}, \\sqrt[n]{x}\n"
            "Derivatives & Limits: \\frac{df}{dx}, f'(x), \\lim_{x \\to \\infty} f(x)\n"
            "Matrices: \\begin{bmatrix} a & b \\\\ c & d \\end{bmatrix}, \\begin{pmatrix} 1 & 2 \\\\ 3 & 4 \\end{pmatrix}\n"
            "Brackets: \\left( x \\right), \\left[ x \\right), \\left\\{ x \\right\\}\n"
            "Piecewise: f(x) = \\begin{cases} x^2 & x \\geq 0 \\\\ -x & x < 0 \\end{cases}\n"
            "Other: \\binom{n}{k}, \\frac{\\partial f}{\\partial x}\n"
            "Greek (lowercase): \\alpha, \\beta, \\gamma, \\delta, \\epsilon, \\theta, \\lambda, \\mu, \\pi, \\sigma, \\phi, \\omega\n"
            "Greek (uppercase): \\Gamma, \\Delta, \\Theta, \\Lambda, \\Pi, \\Sigma, \\Phi, \\Omega\n"
            "Relations & Sets: \\leq, \\geq, \\neq, \\approx, \\in, \\subset, \\cap, \\cup\n"
            "Logic & Other: \\exists, \\forall, \\Rightarrow, \\infty, \\partial, \\nabla\n"
            "\n\nReturn your response in this exact format:\n\n"
            "[DESCRIPTION]\n"
            "Write a natural, friendly response in Korean (1-2 sentences) confirming what you did for the user. "
            "DO NOT explain the code or technical details. "
            "Speak like a helpful assistant confirming the task (e.g., '네, 요청하신 대로 이차방정식 수식을 작성했습니다. 더 필요한 게 있으시면 말씀해주세요!'). "
            "Be conversational and end with an offer to help more.\n"
            "[/DESCRIPTION]\n\n"
            "[CODE]\nOnly the essential lines of code for the requested task, without any boilerplate, classes, functions, or extra comments unless explicitly requested. Be as brief as possible. You can add comment in the code in Korean\n[/CODE]"
        )
        user_message = (
            f"User request: {description}\n\n"
            f"{f'Additional context:{context}' if context else ''}\n\n"
            "Generate minimal Python code for this request. "
            "In the DESCRIPTION section, write a natural conversational response confirming what you did (not technical explanation). "
            "Follow the format strictly: [DESCRIPTION]...natural response...[/DESCRIPTION] and [CODE]...code...[/CODE]"
        )

        try:
            if on_thought:
                on_thought("스크립트 생성 중")
            
            print("[ChatGPT] Generating script...")
            
            # Combine system prompt and user message for gpt-5-nano
            full_prompt = f"{system_prompt}\n\n{user_message}"
            generated = self._call_api_with_retry(full_prompt)
            
            if not generated:
                if on_thought:
                    on_thought(f"❌ 오류 발생: API 응답 없음")
                print("[ChatGPT] ERROR: No response from API")
                return None
            
            print(f"[ChatGPT] Script generated successfully ({len(generated)} characters)")
            return generated
        except Exception as e:
            if on_thought:
                on_thought(f"❌ 오류 발생: {type(e).__name__}")
            print(f"[ChatGPT] ERROR generating script: {type(e).__name__}: {e}")
            return None

    def optimize_script(self, script: str, feedback: str = "", on_thought: Optional[Callable[[str], None]] = None) -> Optional[str]:
        """Optimize an existing script based on feedback.
        
        Args:
            script: The script to optimize
            feedback: Optional feedback about what to improve
            on_thought: Optional callback function to receive thought process updates
            
        Returns:
            Optimized Python script or None if failed
        """
        if not self.is_available():
            return None

        system_prompt = (
            "You are an expert Python developer specializing in HWP automation scripts. "
            "Your task is to simplify and optimize Python scripts for HWP document automation. "
            "Make the code as simple and minimal as possible, removing unnecessary complexity, boilerplate, and redundant steps. "
            "Prioritize brevity, clarity, and directness. Apply the user's feedback for simplification. "
            "- insert_text(text: str): Insert text into the document (텍스트) "
            "- insert_paragraph(): Insert a paragraph break "
            "- insert_equation(latex: str, font_size_pt: float = 14.0): Insert LaTeX equations (벡터, 행렬, 시그마, 미분, 적분 등) "
            "- insert_hwpeqn(hwpeqn: str, font_size_pt: float = 12.0, eq_font_name: str = 'HYhwpEQ'): Insert HWP equation format "
            "- insert_image(image_path: str): Insert an image into the document "
            "- insert_table(rows: int, cols: int, treat_as_char: bool = False, cell_data: list = None): Insert a table/chart (표). "
            "  Example with data: insert_table(rows=3, cols=2, cell_data=[['Header1', 'Header2'], ['Data1', 'Data2'], ['Data3', 'Data4']]) "
            "\n\nLaTeX Reference Guide:\n"
            "Basic Formulas: x = \\frac{-b \\pm \\sqrt{b^2-4ac}}{2a}, E = mc^2\n"
            "Integrals: \\int_{0}^{\\infty} e^{-x^2} dx, \\int x^n dx = \\frac{x^{n+1}}{n+1}\n"
            "Sum & Product: \\sum_{i=1}^{n} i = \\frac{n(n+1)}{2}, \\prod_{i=1}^{n} a_i\n"
            "Fractions & Roots: \\frac{a}{b}, \\sqrt{x}, \\sqrt[n]{x}\n"
            "Derivatives & Limits: \\frac{df}{dx}, f'(x), \\lim_{x \\to \\infty} f(x)\n"
            "Matrices: \\begin{bmatrix} a & b \\\\ c & d \\end{bmatrix}, \\begin{pmatrix} 1 & 2 \\\\ 3 & 4 \\end{pmatrix}\n"
            "Brackets: \\left( x \\right), \\left[ x \\right), \\left\\{ x \\right\\}\n"
            "Piecewise: f(x) = \\begin{cases} x^2 & x \\geq 0 \\\\ -x & x < 0 \\end{cases}\n"
            "Other: \\binom{n}{k}, \\frac{\\partial f}{\\partial x}\n"
            "Greek (lowercase): \\alpha, \\beta, \\gamma, \\delta, \\epsilon, \\theta, \\lambda, \\mu, \\pi, \\sigma, \\phi, \\omega\n"
            "Greek (uppercase): \\Gamma, \\Delta, \\Theta, \\Lambda, \\Pi, \\Sigma, \\Phi, \\Omega\n"
            "Relations & Sets: \\leq, \\geq, \\neq, \\approx, \\in, \\subset, \\cap, \\cup\n"
            "Logic & Other: \\exists, \\forall, \\Rightarrow, \\infty, \\partial, \\nabla\n"
            "\n\nReturn your response in this exact format:\n\n"
            "[DESCRIPTION]\n"
            "Write a natural, friendly response in Korean (1-2 sentences) confirming what you did for the user. "
            "DO NOT explain the code or technical details. "
            "Speak like a helpful assistant confirming the task (e.g., '네, 요청하신 대로 코드를 개선했습니다. 더 필요한 게 있으시면 말씀해주세요!'). "
            "Be conversational and end with an offer to help more.\n"
            "[/DESCRIPTION]\n\n"
            "[CODE]\nOnly the simplified and optimized code\n[/CODE]"
        )
        user_message = (
            f"Simplify and optimize this HWP automation script:\n\n"
            f"```python\n{script}\n```\n\n"
            f"{f'User feedback: {feedback}' if feedback else 'Make the code as simple and minimal as possible.'}\n\n"
            "In the DESCRIPTION section, write a natural conversational response confirming what you did (not technical explanation). "
            "Follow the format strictly: [DESCRIPTION]...natural response...[/DESCRIPTION] and [CODE]...code...[/CODE]"
        )

        try:
            if on_thought:
                on_thought("스크립트 최적화 중")
            
            print("[ChatGPT] Optimizing script...")
            
            # Combine system prompt and user message for gpt-5-nano
            full_prompt = f"{system_prompt}\n\n{user_message}"
            optimized = self._call_api_with_retry(full_prompt)
            
            if not optimized:
                if on_thought:
                    on_thought(f"❌ 오류 발생: API 응답 없음")
                print("[ChatGPT] ERROR: No response from API")
                return None
            
            print(f"[ChatGPT] Script optimized successfully ({len(optimized)} characters)")
            return optimized
        except Exception as e:
            if on_thought:
                on_thought(f"❌ 오류 발생: {type(e).__name__}")
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
