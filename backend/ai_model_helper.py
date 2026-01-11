
"""Multi-model AI integration for script generation and optimization."""

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
    # Models that support vision (image input)
    VISION_MODELS = [
        "gpt-4-vision-preview",  # Example OpenAI vision model
        "gpt-4-vision",          # Alias for vision
        "gemini-2.0-flash",      # Gemini supports vision
        "claude-3-haiku",        # Claude vision
        # Add more as needed
    ]
    """Helper class for multi-model AI API integration (GPT, Gemini, Grok, Claude)."""
    
    # Model pricing per 1M tokens (input/output) - using cheapest models
    PRICING = {
        "gpt-5-nano": {"input": 0.150, "output": 0.600},
        "gpt-5-mini": {"input": 0.200, "output": 0.800},
        "gemini-2.0-flash": {"input": 0.075, "output": 0.300},
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
                self.gemini_model = genai.GenerativeModel("gemini-2.0-flash")
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
        
        # Priority order: GPT (most reliable) → Grok (real-time) → Claude → Gemini
        if self.openai_client:
            models.append((
                "gpt-5-nano",
                "GPT-5 Nano — 빠르고 저렴한 범용 모델",
                self.PRICING["gpt-5-nano"]["input"]
            ))
        
        if self.xai_client:
            models.append((
                "grok-beta",
                "Grok Beta — xAI의 실시간 모델",
                self.PRICING["grok-beta"]["input"]
            ))
        
        if self.anthropic_client:
            models.append((
                "claude-3-haiku",
                "Claude 3 Haiku — 빠르고 정확한 모델",
                self.PRICING["claude-3-haiku"]["input"]
            ))
        
        if self.gemini_model:
            models.append((
                "gemini-2.0-flash",
                "Gemini 2.0 Flash — 최저가 고성능 모델",
                self.PRICING["gemini-2.0-flash"]["input"]
            ))
        
        # Return in priority order (don't sort by price since GPT is cheaper than Grok)
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

    def _call_openai(self, prompt: str, model: str = "gpt-5-nano", image_base64: Optional[str] = None, max_retries: int = 3) -> Optional[str]:
        """Call OpenAI API."""
        if not self.openai_client:
            return None
        
        for attempt in range(max_retries):
            try:
                print(f"[MultiModelAI] Calling OpenAI {model} (attempt {attempt + 1})")
                if image_base64:
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
                        max_completion_tokens=2000
                    )
                else:
                    response = self.openai_client.chat.completions.create(
                        model=model,
                        messages=[{"role": "user", "content": prompt}],
                        max_completion_tokens=2000
                    )
                if response.choices:
                    result = response.choices[0].message.content
                    print(f"[MultiModelAI] OpenAI returned {len(result)} chars")
                    return result
                return None
            except Exception as e:
                error_name = type(e).__name__
                error_msg = str(e)
                print(f"[MultiModelAI] OpenAI {error_name}: {error_msg}")
                if "RateLimitError" in error_name or "rate" in error_msg.lower():
                    if attempt < max_retries - 1:
                        wait_time = 0.5  # Reduced wait time for rate limit
                        print(f"[MultiModelAI] Rate limit, waiting {wait_time}s...")
                        time.sleep(wait_time)
                        continue
                if "model_not_found" in error_msg.lower() or "not found" in error_msg.lower():
                    print(f"[MultiModelAI] Model '{model}' not found. Available models should be checked.")
                    print(f"[MultiModelAI] Full error: {error_msg}")
                if attempt < max_retries - 1:
                    wait_time = 0.2  # Reduced retry wait time
                    print(f"[MultiModelAI] Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                    
        print(f"[MultiModelAI] All {max_retries} attempts failed for model {model}")
        return None

    def _call_anthropic(self, prompt: str, model: str = "claude-3-haiku-20240307", image_base64: Optional[str] = None) -> Optional[str]:
        """Call Anthropic Claude API."""
        if not self.anthropic_client:
            return None
        
        try:
            print(f"[MultiModelAI] Calling Anthropic {model} (image={'yes' if image_base64 else 'no'})")
            
            if image_base64:
                # Vision request - image FIRST, then prompt (important for Claude)
                image_format = "jpeg"
                if image_base64.startswith("iVBORw"):
                    image_format = "png"

                content = [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": f"image/{image_format}",
                            "data": image_base64,
                        },
                    },
                    {"type": "text", "text": prompt},
                ]

                message = self.anthropic_client.messages.create(
                    model=model,
                    max_tokens=2000,
                    messages=[{"role": "user", "content": content}]
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
            print(f"[MultiModelAI] Calling Gemini (image={'yes' if image_path else 'no'})")
            
            if image_path:
                # Vision request - Gemini can take image file directly
                from PIL import Image
                img = Image.open(image_path)
                print(f"[MultiModelAI] Gemini processing image with prompt length: {len(prompt)}")
                response = self.gemini_model.generate_content([prompt, img])
            else:
                # Text-only request
                response = self.gemini_model.generate_content(prompt)
            
            print(f"[MultiModelAI] Gemini response object: {response}")
            print(f"[MultiModelAI] Gemini response.text: {response.text if hasattr(response, 'text') else 'NO TEXT ATTR'}")
            
            # Check for content filtering or safety blocks
            if hasattr(response, 'prompt_feedback'):
                print(f"[MultiModelAI] Gemini prompt_feedback: {response.prompt_feedback}")
            
            if response.text:
                result = response.text
                print(f"[MultiModelAI] Gemini returned {len(result)} chars")
                return result
            else:
                print(f"[MultiModelAI] Gemini returned empty response (no text)")
                # Try to get more details about why
                if hasattr(response, 'candidates') and response.candidates:
                    for idx, candidate in enumerate(response.candidates):
                        print(f"[MultiModelAI] Candidate {idx}: {candidate}")
                        if hasattr(candidate, 'finish_reason'):
                            print(f"[MultiModelAI] Finish reason: {candidate.finish_reason}")
            return None
            
        except Exception as e:
            print(f"[MultiModelAI] Gemini error: {type(e).__name__}: {e}")
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

    def _extract_text_with_ocr(self, image_path: str) -> Optional[str]:
        """Extract text from image using pytesseract OCR."""
        print(f"[MultiModelAI] [OCR] Starting OCR extraction for image: {image_path}")
        try:
            from PIL import Image
            import pytesseract
            img = Image.open(image_path)
            print(f"[MultiModelAI] [OCR] Image loaded successfully.")
            text = pytesseract.image_to_string(img, lang='eng+kor')
            print(f"[MultiModelAI] [OCR] Extracted text:\n{text}")
            return text.strip()
        except Exception as e:
            print(f"[MultiModelAI] [OCR] OCR extraction failed: {e}")
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

        # If image is provided, check if model supports vision
        if image_path:
            # Use Gemini for both image-to-text extraction and answer generation (including HWP file operation)
            print(f"[MultiModelAI] [PROCESS] Using Gemini for full image-based workflow (extraction and answer generation)")
            if not self.gemini_model:
                print(f"[MultiModelAI] [PROCESS] ERROR: Gemini model is not available.")
                return None
            # Use the full prompt for Gemini, not just extraction
            result = self._call_gemini(full_prompt, image_path)
            print(f"[MultiModelAI] [PROCESS] Gemini returned: {result if result else '[NO RESULT]'}")
            return result

        # Ensure vision models receive base64 when an image path is provided
        if image_path and not image_base64:
            if any(vision_id in model for vision_id in self.VISION_MODELS):
                try:
                    image_base64 = self._encode_image_to_base64(image_path)
                    if image_base64:
                        print(f"[MultiModelAI] Encoded image for vision model: {len(image_base64)} bytes")
                except Exception as e:
                    print(f"[MultiModelAI] Failed to encode image for model {model}: {e}")

        # Hard-stop if a vision model was requested with an image but no base64 was produced
        if image_path and any(vision_id in model for vision_id in self.VISION_MODELS) and not image_base64:
            print(f"[MultiModelAI] ERROR: image provided but failed to encode for model {model}")
            return None

        # Route to appropriate API
        print(f"[MultiModelAI] Processing request with model: {model}")
        if "gpt" in model or "gpt-5-nano" in model:
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
        print(f"[MultiModelAI] generate_script called with model='{model}', image_path={image_path}")
        
        if not self.is_available():
            print("[MultiModelAI] ERROR: is_available() returned False")
            return None

        # Detect platform for formula function
        import platform
        is_macos = platform.system() == "Darwin"
        formula_fn = "write_in_formula_editor" if is_macos else "insert_equation"
        formula_syntax = "'formula text'" if is_macos else "'LaTeX formula'"

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
            "\n🚫 CRITICAL: FRACTIONS - Use 'over' syntax!"
            "\n⚠️⚠️⚠️ WHEN YOU SEE '-1-4' or '1-4' → THIS IS A FRACTION, NOT SUBTRACTION!"
            "\n   The pattern 'number-number' in math context = FRACTION with horizontal bar!"
            "\n   '-1-4' means -1 over 4 (negative one quarter)"
            "\n   '1-4' means 1 over 4 (one quarter)"
            "\n✅ For fractions: '{numerator} over {denominator}' - PLAIN TEXT!"
            "\n🔴🔴🔴 CRITICAL - NEVER USE BACKTICKS! 🔴🔴🔴"
            "\n   ❌ WRONG: '{1`over`4}' - NO BACKTICKS!"
            "\n   ❌ WRONG: '{1 `over` 4}' - NO BACKTICKS!"
            "\n   ❌ WRONG: '1over4' - NO SPACES!"
            "\n   ✅ CORRECT: '{1 over 4}' - plain text, spaces, NO backticks"
            "\n   ✅ CORRECT: '{-1 over 4}' - plain text, spaces, NO backticks"
            "\n   ✅ CORRECT: '{3 over 2}' - plain text, spaces, NO backticks"
            "\nWrite the word 'over' as a normal English word with SPACES before and after!"
            "\n✅ CORRECT: f'({{-1} over 4})"
            "\n❌ NEVER use / character: 'a/b' is WRONG!"
            "\n❌ NEVER use minus sign: '1-4' is WRONG when you see a fraction!"
            "\n❌ NEVER write: f'(-1-4) or f'(1-4) - these patterns mean fractions!"
            "\n✅ For square root: 'sqrt {expression}' with curly braces"
            "\n❌ NEVER use parentheses: 'sqrt(...)' is WRONG!"
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
            "\n- write_in_formula_editor(text: str, close_window: bool = True): [macOS ONLY] 수식 삽입 - 모든 수학 공식은 이것 사용! "            "\n  🚨 CRITICAL: ALWAYS use close_window=True to exit the formula editor!"
            "\n  ❌ WRONG: write_in_formula_editor('1 over 4')"
            "\n  ✅ CORRECT: write_in_formula_editor('1 over 4', close_window=True)"            "\n- insert_equation(latex: str, font_size_pt: float = 14.0): Insert complex LaTeX "
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
            "DO NOT list the lines you extracted (no '📋 Line 1:', '📋 Line 2:', etc.). "
            "Speak like a helpful assistant confirming the task (e.g., '네, 요청하신 대로 이차방정식 수식을 작성했습니다. 더 필요한 게 있으시면 말씀해주세요!'). "
            "Be conversational and end with an offer to help more.\n"
            "[/DESCRIPTION]\n\n"
            "[CODE]\nOnly the essential lines of code for the requested task, without any boilerplate, classes, functions, or extra comments unless explicitly requested. Be as brief as possible. You can add comment in the code in Korean\n[/CODE]"
        )
        
        # Build user message
        user_message_parts = [f"User request: {description}"]
        
        if image_path:
            from pathlib import Path
            filename = Path(image_path).name
            user_message_parts.append(
                f"\n\n"
                f"📸 IMAGE PROVIDED: {filename}\n"
                f"\n🚨🚨🚨 YOU ARE OCR SOFTWARE - Extract EVERY SINGLE WORD from the image!\n"
                f"\n⛔ RULE #1: TEXT FIRST, FORMULAS SECOND!\n"
                f"\n⛔ RULE #2: DO NOT SKIP KOREAN TEXT!\n"
                f"\n⛔ RULE #3: DO NOT SKIP QUESTION NUMBERS!\n"
                f"\n⛔ RULE #4: DO NOT SKIP MULTIPLE CHOICE OPTIONS!\n"
                f"\n"
                f"\n� 🔴 🔴 CRITICAL - READ IMAGE FROM TOP TO BOTTOM 🔴 🔴 🔴"
                f"\n"
                f"\nSTEP 1: Look at the TOP of the image FIRST - there is often text ABOVE the formula!"
                f"\nSTEP 2: Extract EVERY line of text you see from top to bottom"
                f"\nSTEP 3: Do NOT skip any text or lines"
                f"\nSTEP 4: Extract ALL content before the formula appears"
                f"\n"
                f"\n� INLINE MATH RULE: Extract math variables/expressions as formulas!"
                f"\nWhen you see text with math like 't=0', 't≥0', 'x', 'P', or numbers like '11':"
                f"\n❌ WRONG: insert_text('11. 시각 t=0일 때')"
                f"\n✅ CORRECT: write_in_formula_editor('11', close_window=True) + insert_text('. 시각 ') + write_in_formula_editor('t=0', close_window=True) + insert_text('일 때')"
                f"\nSplit text and formulas - extract ALL numbers and variables as formulas!"
                f"\n"
                f"\n📝 MANDATORY EXTRACTION ORDER:\n"
                f"\n1. Read TOP of image and extract first line → Split text and inline math!"
                f"\n2. Extract second line → Split text and inline math!"
                f"\n3. Keep extracting ALL text lines BEFORE formula"
                f"\n4. Now extract formula → {formula_fn}(...)"
                f"\n5. Extract ALL text AFTER formula"
                f"\n6. Extract multiple choice options → ⚠️ CRITICAL: ALL OPTIONS ON ONE LINE WITH SPACES"
                f"\n   insert_text('① 6    ② 9    ③ 12    ④ 15    ⑵ 18')"
                f"\n   ❌ WRONG: Each option on separate lines"
                f"\n   ✅ CORRECT: All on ONE line with spacing between options"
                f"\n"
                f"\n🎯 COMPLETE REAL EXAMPLE:"
                f"\n"
                f"\n🚨 CRITICAL: Extract ALL numbers and inline math as formulas!"
                f"\nwrite_in_formula_editor('11', close_window=True)"
                f"\ninsert_text('. 시각 ')"
                f"\nwrite_in_formula_editor('t=0', close_window=True)"
                f"\ninsert_text('일 때 출발하여 수직선 위를 움직이는 점 ')"
                f"\nwrite_in_formula_editor('P', close_window=True)"
                f"\ninsert_text('의')"
                f"\ninsert_paragraph()"
                f"\ninsert_text('시각 ')"
                f"\nwrite_in_formula_editor('t', close_window=True)"
                f"\ninsert_text('(')"
                f"\nwrite_in_formula_editor('t>=0', close_window=True)"
                f"\ninsert_text(')에서의 위치 ')"
                f"\nwrite_in_formula_editor('x', close_window=True)"
                f"\ninsert_text('가')"
                f"\ninsert_paragraph()"
                + (
                    f"\nwrite_in_formula_editor('x = {{t^3}} - {{3 over 2}}{{t^2}} - 6t', close_window=True)"
                    if is_macos
                    else f"\ninsert_equation('x = t^{{3}} - \\\\frac{{3}}{{2}}t^{{2}} - 6t')"
                )
                + f"\ninsert_paragraph()"
                + f"\ninsert_text('이다. 출발한 후 점 P의 운동 방향이 바뀌는 시각에서의')"
                + f"\ninsert_paragraph()"
                + f"\ninsert_text('점 P의 가속도는? [4점]')"
                + f"\ninsert_paragraph()"
                + f"\ninsert_text('① 6    ② 9    ③ 12    ④ 15    ⑤ 18')"
                + f"\ninsert_paragraph()"
                + f"\n"
                + f"\n❌ WRONG (only formula, no text):"
                + f"\nwrite_in_formula_editor(...)"
                + f"\n"
                + f"\n✅ CORRECT (text + formula + text):"
                + f"\ninsert_text('Korean text before')"
                + f"\ninsert_paragraph()"
                + f"\nwrite_in_formula_editor(...)"
                + f"\ninsert_paragraph()"
                + f"\ninsert_text('Korean text after')"
                + f"\n"
                + f"\n🔥 FORMULA SYNTAX ({formula_fn}) - CRITICAL RULES:\n"
                + (
                    f"\n  📌 RULE: ALWAYS wrap powers/superscripts in braces: {{base^power}}"
                    f"\n  📌 RULE: Use 'times' for multiplication, not just number+variable"
                    f"\n  📌 RULE: Separate terms with spaces and operators OUTSIDE braces"
                    f"\n"
                    f"\n  ✅ CORRECT EXAMPLE 1: x = {{t^3}} - 3 - 2{{t^2}} - 6t"
                    f"\n     → This renders as: x = t³ - 3 - 2t² - 6t"
                    f"\n"
                    f"\n  ✅ CORRECT EXAMPLE 2: {{t^3}} - {{3 over 2}}{{t^2}} - 6 times t"
                    f"\n     → This renders as: t³ - (3/2)t² - 6t"
                    f"\n"
                    f"\n  ❌ WRONG: t^3 - 3 - 2t^2 - 6t"
                    f"\n     → HWP renders as: t^(3-3-2t²-6t) (everything becomes superscript!)"
                    f"\n"
                    f"\n  ❌ WRONG: {{t^3 - 3 - 2t^2 - 6t}}"
                    f"\n     → This makes the whole expression a single superscript"
                    f"\n"
                    f"\n  🎯 TEMPLATE for any formula with powers:"
                    f"\n     Variable with power: {{variable^number}}"
                    f"\n     Fraction: {{numerator over denominator}}"
                    f"\n     Multiplication: number times variable"
                    f"\n     Then connect with +, -, etc. OUTSIDE the braces"
                    f"\n"
                    f"\n  Full example code:"
                    f"\n  write_in_formula_editor('x = {{t^3}} - 3 - 2{{t^2}} - 6t', close_window=True)"
                    if is_macos
                    else f"\n  ✅ Windows: insert_equation('x = t^{{3}} - 3 - 2t^{{2}} - 6t')"
                )
                + f"\n"
                + f"\n❌ NEVER SKIP TEXT - Extract Korean/English/numbers AS TEXT!"
                + f"\n❌ NEVER extract only formulas - extract COMPLETE content!"
                + f"\n✅ Read image top to bottom and extract EVERYTHING you see!"
                + f"\n"
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
                
                # Add explicit instruction for image analysis
                image_instruction = (
                    "\n\n� 🔴 🔴 READ THE ENTIRE IMAGE TOP TO BOTTOM - DO NOT SKIP ANYTHING 🔴 🔴 🔴"
                    "\n"
                    "\n⚠️⚠️⚠️ CRITICAL: Images usually have MULTIPLE LINES. You must read ALL of them."
                    "\n"
                    "\nBEFORE WRITING ANY CODE, you MUST list what you see:"
                    "\n- Line 1: [Look at very TOP of image - what text is there?]"
                    "\n- Line 2: [What comes next?]"
                    "\n- Line 3: [Continue down]"
                    "\n"
                    "\n🚨 SPECIAL WARNING FOR KOREAN TEXT 🚨"
                    "\nIf you see Korean text like '11. 시각 t=0일 때...' at the top, that is LINE 1!"
                    "\nDo NOT skip it. Extract it with insert_text()."
                    "\n"
                    "\n� FRACTION RECOGNITION 🚨"
                    "\n⚠️⚠️⚠️ MOST CRITICAL: When you see expressions like '-1-4' or '1-4' in math context:"
                    "\nTHIS IS A FRACTION, NOT SUBTRACTION!"
                    "\nThe middle dash is a FRACTION BAR, not a minus sign!"
                    "\n"
                    "\n🚫🚫🚫 ABSOLUTELY NO BACKTICKS AROUND 'over'! 🚫🚫🚫"
                    "\n❌ WRONG: '{1`over`4}' - BACKTICKS NOT ALLOWED!"
                    "\n❌ WRONG: '{1 `over` 4}' - BACKTICKS NOT ALLOWED!"
                    "\n❌ WRONG: write_in_formula_editor('-1-4')"
                    "\n✅ CORRECT: '{1 over 4}' - plain text only"
                    "\n✅ CORRECT: '{-1 over 4}' - plain text only"
                    "\n✅ CORRECT: f prime ({{{{-1} over 4}})"
                    "\n"
                    "\nThe word 'over' MUST be plain English text with spaces:"
                    "\n  {{1 over 4}}    ← YES, write like this"
                    "\n  {{-1 over 4}}   ← YES, write like this"
                    "\n  {{3 over 2}}    ← YES, write like this"
                    "\n  {{1`over`4}}    ← NO! Backticks forbidden!"
                    "\n  {{1`over`4}}    ← NO! Backticks forbidden!"
                    "\n"
                    "\nWhen you see numbers arranged VERTICALLY or with a horizontal bar:"
                    "\n  -1"
                    "\n  ——  → This is {{-1} over 4}"
                    "\n   4"
                    "\n"
                    "\nCommon fraction patterns to recognize:"
                    "\n• '-1-4' → '{{-1} over 4}'"
                    "\n• '1-4' → '{{1} over 4}'"
                    "\n• '3-2' → '{{3} over 2}'"
                    "\n• Any 'number-number' in parentheses → fraction!"
                    "\n"
                    "\n�👁️ STEP-BY-STEP:"
                    "\n1. Look at the TOP-LEFT of the image"
                    "\n2. Read the FIRST word/character you see"
                    "\n3. Continue reading RIGHT and DOWN"
                    "\n4. When you reach the end of a line, go to the NEXT line"
                    "\n5. Extract EVERY line as insert_text()"
                    "\n6. Keep going until you see a formula"
                    "\n7. Then extract the formula"
                    "\n8. Then continue with any text AFTER the formula"
                    "\n9. If multiple choice exists, combine ALL on ONE line like: insert_text('① 16    ② 29    ③ 12    ④ 15    ⑤ 18')"
                    "\n"
                    "\n✅ DO NOT FORGET THE FIRST LINE! It's the most important!"
                    "\n✅ DO NOT SKIP ANY LINES!"
                    "\n✅ READ FROM TOP TO BOTTOM!"
                    "\n✅ MULTIPLE CHOICE: ALL OPTIONS ON ONE LINE WITH SPACING!"                    "\n"
                    "\n🚨 CRITICAL: ALWAYS include close_window=True! 🚨"
                    "\nEvery write_in_formula_editor() call MUST have close_window=True"
                    "\n❌ WRONG: write_in_formula_editor('1 over 4')"
                    "\n✅ CORRECT: write_in_formula_editor('1 over 4', close_window=True)"                )
                full_prompt = f"{system_prompt}{image_instruction}\n\n{user_message}"
            else:
                full_prompt = f"{system_prompt}\n\n{user_message}"
            print(f"[MultiModelAI] Calling API with model={model}...")
            generated = self._call_api_with_retry(
                full_prompt, 
                model=model,
                image_base64=image_base64,
                image_path=image_path
            )
            
            if not generated:
                if on_thought:
                    on_thought(f"❌ 오류 발생: API 응답 없음")
                print(f"[MultiModelAI] ERROR: API returned None for model={model}")
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

