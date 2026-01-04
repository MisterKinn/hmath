"""Multi-model AI integration for script generation and optimization."""

from __future__ import annotations

import os
import time
import base64
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

try:
    import anthropic  # type: ignore[import]
except ImportError:
    anthropic = None  # type: ignore[assignment]

try:
    import google.generativeai as genai  # type: ignore[import]
except ImportError:
    genai = None  # type: ignore[assignment]


class MultiModelAIHelper:
    """Helper class for multi-model AI API integration (GPT, Gemini, Grok, Claude)."""
    
    # Model pricing per 1M tokens (input/output) - using cheapest models
    PRICING = {
        "gpt-4o-mini": {"input": 0.150, "output": 0.600},
        "gemini-1.5-flash": {"input": 0.075, "output": 0.300},
        "grok-beta": {"input": 5.000, "output": 15.000},  # Currently expensive
        "claude-3-haiku": {"input": 0.250, "output": 1.250},
    }

    def __init__(self, api_keys: Optional[dict] = None) -> None:
        """Initialize multi-model AI helper.
        
        Args:
            api_keys: Dict of API keys with model names as keys. 
                     If not provided, will try to get from env vars or .env file.
        """
        # Load .env file from project root
        if load_dotenv is not None:
            env_path = Path(__file__).resolve().parents[1] / ".env"
            print(f"[MultiModelAI] Looking for .env at: {env_path}")
            if env_path.exists():
                print(f"[MultiModelAI] .env file found!")
                load_dotenv(dotenv_path=env_path)
            else:
                print(f"[MultiModelAI] .env file not found at {env_path}")
        else:
            print("[MultiModelAI] python-dotenv not installed, skipping .env file")
        
        # Initialize API keys
        self.api_keys = api_keys or {}
        self.api_keys.setdefault("openai", os.getenv("OPENAI_API_KEY"))
        self.api_keys.setdefault("anthropic", os.getenv("ANTHROPIC_API_KEY"))
        self.api_keys.setdefault("google", os.getenv("GOOGLE_API_KEY"))
        self.api_keys.setdefault("xai", os.getenv("XAI_API_KEY"))
        
        # Initialize clients
        self.openai_client = None
        self.anthropic_client = None
        self.gemini_model = None
        self.xai_client = None
        
        # Initialize OpenAI (GPT)
        if self.api_keys.get("openai") and OpenAI is not None:
            try:
                self.openai_client = OpenAI(api_key=self.api_keys["openai"])
                print("[MultiModelAI] OpenAI client initialized!")
            except Exception as e:
                print(f"[MultiModelAI] Failed to initialize OpenAI: {e}")
        
        # Initialize Anthropic (Claude)
        if self.api_keys.get("anthropic") and anthropic is not None:
            try:
                self.anthropic_client = anthropic.Anthropic(api_key=self.api_keys["anthropic"])
                print("[MultiModelAI] Anthropic client initialized!")
            except Exception as e:
                print(f"[MultiModelAI] Failed to initialize Anthropic: {e}")
        
        # Initialize Google (Gemini)
        if self.api_keys.get("google") and genai is not None:
            try:
                genai.configure(api_key=self.api_keys["google"])
                self.gemini_model = genai.GenerativeModel("gemini-1.5-flash")
                print("[MultiModelAI] Gemini client initialized!")
            except Exception as e:
                print(f"[MultiModelAI] Failed to initialize Gemini: {e}")
        
        # Initialize xAI (Grok) - uses OpenAI-compatible API
        if self.api_keys.get("xai") and OpenAI is not None:
            try:
                self.xai_client = OpenAI(
                    api_key=self.api_keys["xai"],
                    base_url="https://api.x.ai/v1"
                )
                print("[MultiModelAI] xAI (Grok) client initialized!")
            except Exception as e:
                print(f"[MultiModelAI] Failed to initialize xAI: {e}")

    def get_available_models(self) -> list[tuple[str, str, float]]:
        """Get list of available models with their names, descriptions, and costs.
        
        Returns:
            List of (model_id, description, cost_per_1M_tokens)
        """
        models = []
        
        if self.openai_client:
            models.append((
                "gpt-4o-mini",
                "GPT-4o Mini — 빠르고 저렴한 범용 모델",
                self.PRICING["gpt-4o-mini"]["input"]
            ))
        
        if self.gemini_model:
            models.append((
                "gemini-1.5-flash",
                "Gemini 1.5 Flash — 최저가 고성능 모델",
                self.PRICING["gemini-1.5-flash"]["input"]
            ))
        
        if self.anthropic_client:
            models.append((
                "claude-3-haiku",
                "Claude 3 Haiku — 빠르고 정확한 모델",
                self.PRICING["claude-3-haiku"]["input"]
            ))
        
        if self.xai_client:
            models.append((
                "grok-beta",
                "Grok Beta — xAI의 실시간 모델",
                self.PRICING["grok-beta"]["input"]
            ))
        
        # Sort by price (cheapest first)
        models.sort(key=lambda x: x[2])
        return models
    
    def get_cheapest_model(self) -> Optional[str]:
        """Get the cheapest available model.
        
        Returns:
            Model ID of the cheapest model, or None if no models available
        """
        models = self.get_available_models()
        return models[0][0] if models else None

    def is_available(self) -> bool:
        """Check if at least one AI model is available."""
        return any([
            self.openai_client,
            self.anthropic_client,
            self.gemini_model,
            self.xai_client
        ])

    def _encode_image_to_base64(self, image_path: str) -> Optional[str]:
        """Encode image file to base64 string."""
        try:
            from pathlib import Path
            file_path = Path(image_path)
            
            # If it's a PDF, convert first page to image
            if file_path.suffix.lower() == '.pdf':
                print(f"[MultiModelAI] Converting PDF to image...")
                try:
                    from pdf2image import convert_from_path
                    images = convert_from_path(image_path, first_page=1, last_page=1)
                    if images:
                        import io
                        img_byte_arr = io.BytesIO()
                        images[0].save(img_byte_arr, format='PNG')
                        img_byte_arr = img_byte_arr.getvalue()
                        encoded = base64.b64encode(img_byte_arr).decode('utf-8')
                        print(f"[MultiModelAI] PDF converted and encoded: {len(encoded)} bytes")
                        return encoded
                except ImportError:
                    print("[MultiModelAI] pdf2image not installed")
                    return None
                except Exception as e:
                    print(f"[MultiModelAI] Error converting PDF: {e}")
                    return None
            else:
                # Regular image file
                with open(image_path, "rb") as image_file:
                    encoded = base64.b64encode(image_file.read()).decode('utf-8')
                    print(f"[MultiModelAI] Image encoded: {len(encoded)} bytes")
                    return encoded
        except Exception as e:
            print(f"[MultiModelAI] Failed to encode image: {e}")
            return None

    def _call_openai(self, prompt: str, model: str = "gpt-4o-mini", image_base64: Optional[str] = None, max_retries: int = 3) -> Optional[str]:
        """Call OpenAI API."""
        if not self.openai_client:
            return None
        
        for attempt in range(max_retries):
            try:
                print(f"[MultiModelAI] Calling OpenAI {model} (attempt {attempt + 1})")
                
                if image_base64:
                    # Vision request
                    image_format = "jpeg"
                    if image_base64.startswith("/9j/"):
                        image_format = "jpeg"
                    elif image_base64.startswith("iVBORw"):
                        image_format = "png"
                    
                    messages = [{
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {"type": "image_url", "image_url": {"url": f"data:image/{image_format};base64,{image_base64}"}}
                        ]
                    }]
                    
                    response = self.openai_client.chat.completions.create(
                        model=model,
                        messages=messages,
                        max_tokens=2000
                    )
                else:
                    # Text-only request
                    response = self.openai_client.chat.completions.create(
                        model=model,
                        messages=[{"role": "user", "content": prompt}],
                        max_tokens=2000
                    )
                
                if response.choices:
                    result = response.choices[0].message.content
                    print(f"[MultiModelAI] OpenAI returned {len(result)} chars")
                    return result
                return None
                
            except Exception as e:
                error_name = type(e).__name__
                if "RateLimitError" in error_name or "rate" in str(e).lower():
                    if attempt < max_retries - 1:
                        wait_time = (2 ** attempt) + 1
                        print(f"[MultiModelAI] Rate limit, waiting {wait_time}s...")
                        time.sleep(wait_time)
                        continue
                print(f"[MultiModelAI] OpenAI error: {e}")
                return None
        return None

    def _call_anthropic(self, prompt: str, model: str = "claude-3-haiku-20240307", image_base64: Optional[str] = None) -> Optional[str]:
        """Call Anthropic Claude API."""
        if not self.anthropic_client:
            return None
        
        try:
            print(f"[MultiModelAI] Calling Anthropic {model}")
            
            if image_base64:
                # Vision request
                image_format = "jpeg"
                if image_base64.startswith("iVBORw"):
                    image_format = "png"
                
                message = self.anthropic_client.messages.create(
                    model=model,
                    max_tokens=2000,
                    messages=[{
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": f"image/{image_format}",
                                    "data": image_base64,
                                },
                            },
                            {"type": "text", "text": prompt}
                        ],
                    }]
                )
            else:
                # Text-only request
                message = self.anthropic_client.messages.create(
                    model=model,
                    max_tokens=2000,
                    messages=[{"role": "user", "content": prompt}]
                )
            
            if message.content:
                result = message.content[0].text
                print(f"[MultiModelAI] Anthropic returned {len(result)} chars")
                return result
            return None
            
        except Exception as e:
            print(f"[MultiModelAI] Anthropic error: {e}")
            return None

    def _call_gemini(self, prompt: str, image_path: Optional[str] = None) -> Optional[str]:
        """Call Google Gemini API."""
        if not self.gemini_model:
            return None
        
        try:
            print(f"[MultiModelAI] Calling Gemini")
            
            if image_path:
                # Vision request - Gemini can take image file directly
                from PIL import Image
                img = Image.open(image_path)
                response = self.gemini_model.generate_content([prompt, img])
            else:
                # Text-only request
                response = self.gemini_model.generate_content(prompt)
            
            if response.text:
                result = response.text
                print(f"[MultiModelAI] Gemini returned {len(result)} chars")
                return result
            return None
            
        except Exception as e:
            print(f"[MultiModelAI] Gemini error: {e}")
            return None

    def _call_grok(self, prompt: str, model: str = "grok-beta") -> Optional[str]:
        """Call xAI Grok API (OpenAI-compatible)."""
        if not self.xai_client:
            return None
        
        try:
            print(f"[MultiModelAI] Calling Grok {model}")
            
            response = self.xai_client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=2000
            )
            
            if response.choices:
                result = response.choices[0].message.content
                print(f"[MultiModelAI] Grok returned {len(result)} chars")
                return result
            return None
            
        except Exception as e:
            print(f"[MultiModelAI] Grok error: {e}")
            return None

    def _call_api_with_retry(
        self, 
        full_prompt: str, 
        model: str = "auto",
        image_base64: Optional[str] = None,
        image_path: Optional[str] = None,
        max_retries: int = 3
    ) -> Optional[str]:
        """Call AI API with automatic model selection and retry logic.
        
        Args:
            full_prompt: The full prompt to send
            model: Model to use ("auto" for cheapest, or specific model name)
            image_base64: Optional base64 encoded image
            image_path: Optional image file path (for Gemini)
            max_retries: Maximum retries for rate limits
        
        Returns:
            API response or None
        """
        # Auto-select cheapest model
        if model == "auto":
            model = self.get_cheapest_model()
            if not model:
                print("[MultiModelAI] No models available")
                return None
            print(f"[MultiModelAI] Auto-selected cheapest model: {model}")
        
        # Route to appropriate API
        if "gpt" in model or "gpt-4o-mini" in model:
            return self._call_openai(full_prompt, model, image_base64, max_retries)
        elif "claude" in model or "haiku" in model:
            return self._call_anthropic(full_prompt, model, image_base64)
        elif "gemini" in model or "flash" in model:
            return self._call_gemini(full_prompt, image_path)
        elif "grok" in model:
            return self._call_grok(full_prompt, model)
        else:
            print(f"[MultiModelAI] Unknown model: {model}")
            return None

    def generate_script(
        self, 
        description: str, 
        context: str = "", 
        image_path: Optional[str] = None,
        on_thought: Optional[Callable[[str], None]] = None,
        model: str = "auto"
    ) -> Optional[str]:
        """Generate a Python script based on description.
        
        Args:
            description: Description of what the script should do
            context: Additional context
            image_path: Optional image file path
            on_thought: Optional callback for thought updates
            model: Model to use ("auto" for cheapest)
        
        Returns:
            Generated Python script or None if failed
        """
        if not self.is_available():
            return None

        # Same system prompt as chatgpt_helper.py
        system_prompt = (
            "You are an expert Python developer specializing in HWP (한글) automation scripts. "
            "\n\n"
            "\n🚨🚨🚨 ABSOLUTE PROHIBITION - READ THIS FIRST! 🚨🚨🚨"
            "\n"
            "\n❌❌❌ THE FUNCTION insert_image() DOES NOT EXIST! ❌❌❌"
            "\n❌❌❌ NEVER WRITE: insert_image('/path/to/file') ❌❌❌"
            "\n❌❌❌ NEVER WRITE: insert_image(file_path) ❌❌❌"
            "\n❌❌❌ NEVER WRITE: insert_image(image_path) ❌❌❌"
            "\n❌❌❌ ANY CODE WITH insert_image IS 100% WRONG! ❌❌❌"
            "\n"
            "\n✅ When user uploads image/PDF: READ it, EXTRACT content, DON'T insert file!"
            "\n✅ For formulas in image: Use write_in_formula_editor()"
            "\n✅ For text in image: Use insert_text()"
            "\n✅ For layout: Use insert_paragraph()"
            "\n"
            "\n🚨 If you write insert_image(), the script will FAIL! 🚨"
            "\n"
            "\n\n📸 IMAGE & FORMULA RECOGNITION:"
            "\nWhen user provides an image or PDF with mathematical formulas:"
            "\n1. CAREFULLY read and understand ALL mathematical formulas in the image"
            "\n2. PRESERVE the original layout - line breaks, paragraphs, spacing"
            "\n3. Recognize LaTeX-style formulas like \\frac{a}{b}, \\sqrt{x}, x^2, \\int, \\sum, etc."
            "\n4. Convert formulas to HWP 수식 입력기 format using write_in_formula_editor()"
            "\n5. If image contains multiple lines/paragraphs, use insert_paragraph() between them"
            "\n6. Preserve the exact mathematical structure and symbols from the image"
            "\n"
            "\n🚫🚫🚫 CRITICAL RULE #1: FRACTIONS - NEVER USE / CHARACTER! 🚫🚫🚫"
            "\nWhen writing ANY fraction in write_in_formula_editor(): "
            "\n✅ CORRECT: Use 'over' → Example: 'a over b', '(x+1) over (y+2)' "
            "\n❌ WRONG: NEVER use / → Example: 'a/b', '(x+1)/(y+2)' are FORBIDDEN! "
            "\n❌ WRONG: NEVER use ÷ → Example: 'a÷b' is FORBIDDEN! "
            "\n\n📖 FRACTION SYNTAX RULES: "
            "\n1. Format: (entire_numerator) over (entire_denominator) "
            "\n2. ALWAYS use parentheses for complex expressions "
            "\n3. For nested fractions, each fraction uses its own 'over' "
            "\n\n📝 FRACTION EXAMPLES: "
            "\n- Simple: a/b → 'a over b' "
            "\n- Complex: (a+b)/(c+d) → '{a+b} over {c+d}' "
            "\n- With multiplication: (2*a*b)/(3*c) → '{2 times a times b} over {3 times c}' "
            "\n"
            "\n🎯 QUADRATIC FORMULA (근의 공식) - MOST IMPORTANT EXAMPLE:"
            "\n   Mathematical notation: x = [-b ± √(b²-4ac)] / (2a)"
            "\n"
            "\n   Structure breakdown:"
            "\n   ┌─────────────────────────────────────┐"
            "\n   │  NUMERATOR (분자):                  │"
            "\n   │  -b ± √(b²-4ac)  ← ENTIRE top part │"
            "\n   ├─────────────────────────────────────┤"
            "\n   │  'over'  ← separator                │"
            "\n   ├─────────────────────────────────────┤"
            "\n   │  DENOMINATOR (분모):                │"
            "\n   │  2a  ← ENTIRE bottom part           │"
            "\n   └─────────────────────────────────────┘"
            "\n"
            "\n   ✅ CORRECT: 'x = {-b +- sqrt {b^2 - 4 times a times c}} over {2 times a}'"
            "\n   ❌ WRONG: 'x = {-b +- sqrt(b^2 - 4 times a times c)} over {2 times a}' ← Use sqrt {...} not sqrt(...)!"
            "\n   ❌ WRONG: 'x = (-b +- sqrt(...)) over (2 times a)' ← Use {} not ()!"
            "\n   ❌ WRONG: 'x = (-b +- sqrt(...)) / (2 times a)' ← NO / character!"
            "\n   ❌ WRONG: 'x = -b over 2a +- sqrt(...) over 2a' ← NO! This creates TWO fractions!"
            "\n   ❌ WRONG: Any structure with / character ← NO!"
            "\n"
            "\n   🔑 Use curly braces {} for ALL grouping - NEVER use parentheses ()!"
            "\n   🔑 sqrt {...} NOT sqrt(...) - Use {} even inside sqrt!"
            "\n"
            "\n⚠️⚠️⚠️ CRITICAL RULE #2: ALWAYS USE FORMULA EDITOR FOR MATH! "
            "If user asks for ANYTHING related to: "
            "- 수식 (formula), 방정식 (equation), 공식 (formula), 해 (solution) "
            "- Any equation like y=x, f(x)=, ax^2+bx+c= "
            "- Mathematical expressions, formulas, or equations "
            "- 1차방정식, 2차방정식, 3차방정식, n차방정식 "
            "- 근의 공식, quadratic formula, cubic formula "
            "- 함수 표현 like y=f(x), y=2x+1 "
            "YOU MUST USE write_in_formula_editor() - NEVER use insert_text()! "
            "Even for simple math like 'y=x+1', use write_in_formula_editor('y=x+1', close_window=True) "
            "DO NOT write math as plain text with insert_text()! ⚠️⚠️⚠️"
            "\n\n"
            "Your task is to generate only the minimal Python code needed for the user's request, using ONLY these functions: "
            "\n"
            "✅ AVAILABLE FUNCTIONS (사용 가능한 함수):"
            "\n- insert_text(text: str): Insert plain text (일반 텍스트 삽입, 수식 아님!) "
            "\n- insert_paragraph(): Insert a paragraph break (문단 나누기) "
            "\n- write_in_formula_editor(text: str, close_window: bool = True): [macOS ONLY] 수식 삽입 - 모든 수학 공식은 이것 사용! "
            "\n- insert_equation(latex: str, font_size_pt: float = 14.0): Insert complex LaTeX "
            "\n- insert_hwpeqn(hwpeqn: str, font_size_pt: float = 12.0): Insert HWP equation format "
            "\n- insert_table(rows: int, cols: int, cell_data: list = None): Insert a table "
            "\n"
            "\n🚫🚫🚫 FUNCTIONS THAT DO NOT EXIST (존재하지 않는 함수 - 절대 사용 금지!):"
            "\n❌ insert_image() ← THIS DOES NOT EXIST! 이 함수는 존재하지 않습니다!"
            "\n❌ insert_picture() ← THIS DOES NOT EXIST!"
            "\n❌ insert_file() ← THIS DOES NOT EXIST!"
            "\n❌ add_image() ← THIS DOES NOT EXIST!"
            "\n"
            "\n🚨 IF YOU WRITE insert_image() OR ANY IMAGE INSERTION CODE, THE SCRIPT WILL CRASH! 🚨"
            "\n"
            "\nReturn your response in this exact format:\n\n"
            "[DESCRIPTION]\n"
            "Write a natural, friendly response in Korean (1-2 sentences) confirming what you did for the user. "
            "DO NOT explain the code or technical details. "
            "Speak like a helpful assistant confirming the task (e.g., '네, 요청하신 대로 이차방정식 수식을 작성했습니다. 더 필요한 게 있으시면 말씀해주세요!'). "
            "Be conversational and end with an offer to help more.\n"
            "[/DESCRIPTION]\n\n"
            "[CODE]\nOnly the essential lines of code for the requested task, without any boilerplate, classes, functions, or extra comments unless explicitly requested. Be as brief as possible. You can add comment in the code in Korean\n[/CODE]"
        )
        
        # Build user message
        user_message_parts = [f"User request: {description}"]
        
        if image_path:
            user_message_parts.append(
                f"\n\n"
                f"\n🚨🚨🚨 STOP! READ THIS BEFORE GENERATING CODE! 🚨🚨🚨"
                f"\n"
                f"\n❌❌❌ DO NOT WRITE: insert_image()"
                f"\n❌❌❌ DO NOT WRITE: insert_image('{image_path}')"
                f"\n❌❌❌ insert_image() DOES NOT EXIST! IT WILL CRASH!"
                f"\n"
                f"\n✅✅✅ YOUR JOB: READ THE IMAGE AND EXTRACT CONTENT"
                f"\n"
                f"\n📋 WHAT YOU SEE IN THE IMAGE:"
                f"\n  - Text? → Use insert_text('text here')"
                f"\n  - Formula? → Use write_in_formula_editor('formula', close_window=True)"
                f"\n  - New line? → Use insert_paragraph()"
                f"\n  - The image file itself? → DO NOTHING! Don't insert it!"
                f"\n"
            )
        
        if context:
            user_message_parts.append(f"\n\nAdditional context: {context}")
        
        user_message_parts.append(
            "\n\nGenerate minimal Python code for this request. "
            "In the DESCRIPTION section, write a natural conversational response confirming what you did (not technical explanation). "
            "Follow the format strictly: [DESCRIPTION]...natural response...[/DESCRIPTION] and [CODE]...code...[/CODE]"
        )
        
        user_message = "".join(user_message_parts)

        try:
            if on_thought:
                on_thought("스크립트 생성 중")
            
            print(f"[MultiModelAI] Generating script with model: {model}")
            
            # Handle image if provided
            image_base64 = None
            if image_path:
                if on_thought:
                    on_thought("이미지 분석 중...")
                print(f"[MultiModelAI] Processing image: {image_path}")
                image_base64 = self._encode_image_to_base64(image_path)
                if not image_base64:
                    if on_thought:
                        on_thought("❌ 이미지 처리 실패")
                    print("[MultiModelAI] ERROR: Failed to encode image")
                    return None
            
            # Combine system prompt and user message
            full_prompt = f"{system_prompt}\n\n{user_message}"
            generated = self._call_api_with_retry(
                full_prompt, 
                model=model,
                image_base64=image_base64,
                image_path=image_path
            )
            
            if not generated:
                if on_thought:
                    on_thought(f"❌ 오류 발생: API 응답 없음")
                print("[MultiModelAI] ERROR: No response from API")
                return None
            
            # Filter out insert_image() calls if AI generated them
            if image_path and "insert_image(" in generated:
                print("[MultiModelAI] ⚠️ WARNING: AI generated insert_image()! Filtering...")
                lines = generated.split('\n')
                filtered_lines = [line for line in lines if 'insert_image(' not in line]
                generated = '\n'.join(filtered_lines)
            
            print(f"[MultiModelAI] Script generated successfully ({len(generated)} characters)")
            return generated
        except Exception as e:
            if on_thought:
                on_thought(f"❌ 오류 발생: {type(e).__name__}")
            print(f"[MultiModelAI] ERROR generating script: {type(e).__name__}: {e}")
            return None

    def optimize_script(
        self, 
        script: str, 
        feedback: str = "", 
        on_thought: Optional[Callable[[str], None]] = None,
        model: str = "auto"
    ) -> Optional[str]:
        """Optimize an existing script based on feedback.
        
        Args:
            script: The script to optimize
            feedback: Optional feedback
            on_thought: Optional callback
            model: Model to use ("auto" for cheapest)
        
        Returns:
            Optimized Python script or None if failed
        """
        if not self.is_available():
            return None

        system_prompt = (
            "You are an expert Python developer specializing in HWP automation scripts. "
            "Your task is to simplify and optimize Python scripts for HWP document automation. "
            "Make the code as simple and minimal as possible, removing unnecessary complexity, boilerplate, and redundant steps. "
            "\n"
            "✅ AVAILABLE FUNCTIONS:"
            "- insert_text(text: str): Insert text "
            "- insert_paragraph(): Insert a paragraph break "
            "- write_in_formula_editor(text: str, close_window: bool = True): Insert formulas "
            "- insert_equation(latex: str, font_size_pt: float = 14.0): Insert LaTeX equations "
            "- insert_hwpeqn(hwpeqn: str, font_size_pt: float = 12.0): Insert HWP equation format "
            "- insert_table(rows: int, cols: int, cell_data: list = None): Insert a table "
            "\n"
            "\n🚫 FUNCTIONS THAT DO NOT EXIST:"
            "- insert_image() ← DOES NOT EXIST!"
            "\n"
            "\nReturn your response in this exact format:\n\n"
            "[DESCRIPTION]\n"
            "Write a natural, friendly response in Korean (1-2 sentences) confirming what you did for the user. "
            "DO NOT explain the code or technical details. "
            "Speak like a helpful assistant confirming the task.\n"
            "[/DESCRIPTION]\n\n"
            "[CODE]\nOnly the simplified and optimized code\n[/CODE]"
        )
        
        user_message = (
            f"Simplify and optimize this HWP automation script:\n\n"
            f"```python\n{script}\n```\n\n"
            f"{f'User feedback: {feedback}' if feedback else 'Make the code as simple and minimal as possible.'}\n\n"
            "Follow the format strictly: [DESCRIPTION]...natural response...[/DESCRIPTION] and [CODE]...code...[/CODE]"
        )

        try:
            if on_thought:
                on_thought("스크립트 최적화 중")
            
            print(f"[MultiModelAI] Optimizing script with model: {model}")
            
            # Combine prompts
            full_prompt = f"{system_prompt}\n\n{user_message}"
            optimized = self._call_api_with_retry(full_prompt, model=model)
            
            if not optimized:
                if on_thought:
                    on_thought(f"❌ 오류 발생: API 응답 없음")
                return None
            
            print(f"[MultiModelAI] Script optimized successfully")
            return optimized
        except Exception as e:
            if on_thought:
                on_thought(f"❌ 오류 발생: {type(e).__name__}")
            print(f"[MultiModelAI] ERROR optimizing script: {e}")
            return None

