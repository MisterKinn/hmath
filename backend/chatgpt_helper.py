"""ChatGPT integration for script generation and optimization."""

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

    def _encode_image_to_base64(self, image_path: str) -> Optional[str]:
        """Encode image file to base64 string.
        
        Args:
            image_path: Path to the image file (supports images and PDFs)
            
        Returns:
            Base64 encoded string or None if failed
        """
        try:
            from pathlib import Path
            file_path = Path(image_path)
            
            # If it's a PDF, convert first page to image
            if file_path.suffix.lower() == '.pdf':
                print(f"[ChatGPT] Converting PDF to image...")
                try:
                    from pdf2image import convert_from_path
                    # Convert only first page
                    images = convert_from_path(image_path, first_page=1, last_page=1)
                    if images:
                        import io
                        # Convert PIL Image to bytes
                        img_byte_arr = io.BytesIO()
                        images[0].save(img_byte_arr, format='PNG')
                        img_byte_arr = img_byte_arr.getvalue()
                        encoded = base64.b64encode(img_byte_arr).decode('utf-8')
                        print(f"[ChatGPT] PDF converted and encoded successfully: {len(encoded)} bytes")
                        return encoded
                    else:
                        print("[ChatGPT] ERROR: No pages found in PDF")
                        return None
                except ImportError:
                    print("[ChatGPT] WARNING: pdf2image not installed, cannot process PDF")
                    print("[ChatGPT] Install with: pip install pdf2image")
                    return None
                except Exception as e:
                    print(f"[ChatGPT] ERROR converting PDF: {type(e).__name__}: {e}")
                    return None
            else:
                # Regular image file
                with open(image_path, "rb") as image_file:
                    encoded = base64.b64encode(image_file.read()).decode('utf-8')
                    print(f"[ChatGPT] Image encoded successfully: {len(encoded)} bytes")
                    return encoded
        except Exception as e:
            print(f"[ChatGPT] Failed to encode image: {type(e).__name__}: {e}")
            return None

    def _call_api_with_retry(self, full_prompt: str, model: str = "gpt-4o", image_base64: Optional[str] = None, max_retries: int = 3) -> Optional[str]:
        """Call OpenAI API with retry logic for rate limits.
        
        Args:
            full_prompt: The full prompt to send to the API
            model: The model to use (default: gpt-4o for vision support)
            image_base64: Optional base64 encoded image for vision requests
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
                
                # Build messages based on whether we have an image
                if image_base64:
                    # Use vision-enabled chat completion
                    print(f"[ChatGPT] Using vision API with image (model: {model})")
                    
                    # Detect image format from base64 header
                    image_format = "jpeg"  # default
                    if image_base64.startswith("/9j/"):
                        image_format = "jpeg"
                    elif image_base64.startswith("iVBORw"):
                        image_format = "png"
                    elif image_base64.startswith("R0lGOD"):
                        image_format = "gif"
                    
                    messages = [
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    "text": full_prompt
                                },
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/{image_format};base64,{image_base64}"
                                    }
                                }
                            ]
                        }
                    ]
                    
                    response = self.client.chat.completions.create(  # type: ignore[union-attr]
                    model=model,
                        messages=messages,
                        max_tokens=2000
                    )
                    
                    if response.choices and len(response.choices) > 0:
                        result = response.choices[0].message.content
                        if result:
                            print(f"[ChatGPT] Vision API returned {len(result)} characters")
                            return result
                        else:
                            print("[ChatGPT] WARNING: Vision API returned empty content")
                            return None
                    else:
                        print("[ChatGPT] WARNING: No choices in response")
                        return None
                else:
                    # Regular text-only request
                    try:
                        response = self.client.responses.create(model="gpt-5-nano", input=full_prompt)
                        if hasattr(response, 'output_text'):
                            result = response.output_text
                            if result:
                                print(f"[ChatGPT] API returned {len(result)} characters")
                                return result
                            else:
                                print("[ChatGPT] WARNING: API returned empty output_text")
                                return None
                        else:
                            print(f"[ChatGPT] WARNING: Response object has no output_text attribute")
                            return None
                    except AttributeError:
                        print("[ChatGPT] Falling back to chat.completions.create")
                        response = self.client.chat.completions.create(model="gpt-4o-mini", messages=[{"role": "user", "content": full_prompt}], max_tokens=2000)
                        if response.choices and len(response.choices) > 0:
                            result = response.choices[0].message.content
                            if result:
                                print(f"[ChatGPT] Chat API returned {len(result)} characters")
                                return result
                        else:
                            print("[ChatGPT] WARNING: No choices in chat response")
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

    def generate_script(
        self, 
        description: str, 
        context: str = "", 
        image_path: Optional[str] = None,
        on_thought: Optional[Callable[[str], None]] = None
    ) -> Optional[str]:
        """Generate a Python script based on description.
        
        Args:
            description: Description of what the script should do
            context: Additional context (e.g., available functions)
            image_path: Optional path to an image file (for vision-based requests)
            on_thought: Optional callback function to receive thought process updates
            
        Returns:
            Generated Python script or None if failed
        """
        if not self.is_available():
            return None

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
            "\n- Nested: (a/b)/(c/d) → '{a over b} over {c over d}' "
            "\n- Three level: a/(b/(c/d)) → 'a over {b over {c over d}}' "
            "\n\n⚠️ REMEMBER: The / character is FORBIDDEN in formula editor! Always 'over'! ⚠️"
            "\n\n⚠️⚠️⚠️ CRITICAL RULE #2: ALWAYS USE FORMULA EDITOR FOR MATH! "
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
            "\n📸 When analyzing images/PDFs:"
            "\n  ✅ DO: Extract text → insert_text('extracted text')"
            "\n  ✅ DO: Extract formulas → write_in_formula_editor('formula', close_window=True)"
            "\n  ✅ DO: Preserve layout → insert_paragraph()"
            "\n  ❌ DON'T: insert_image('/path/to/file') ← CRASH!"
            "\n  ❌ DON'T: Include any file path in code ← WRONG!"
            "\n"            "\n\n⚠️⚠️⚠️ NEVER USE insert_text() FOR FORMULAS/EQUATIONS/MATH! "
            "If request contains: 수식, 방정식, 공식, 해, equation, formula, function, y=, f(x)=, x^2, etc. "
            "→ USE write_in_formula_editor() ONLY! ⚠️⚠️⚠️"
            "\n\n**IMPORTANT FORMULA RULE (macOS ONLY)**: "
            "⚠️⚠️⚠️ MANDATORY: When user asks for ANY mathematical formula, equation, or expression (수식, 방정식, 함수, 공식, 해 등), "
            "you MUST use write_in_formula_editor(text, close_window=True) with KOREAN FORMULA EDITOR SYNTAX. "
            "DO NOT use insert_text() for ANY math-related content! "
            "Even simple equations like 'y=x+1' or '3차방정식' MUST use write_in_formula_editor()! "
            "ALWAYS set close_window=True to automatically click the 넣기 button after writing. "
            "\n\n⚠️⚠️⚠️ Examples requiring write_in_formula_editor() [NOT insert_text()]: "
            "- User: '3차방정식 공식과 해를 구하는 과정을 작성해줘' → write_in_formula_editor('ax^3 + bx^2 + cx + d = 0', close_window=True) "
            "- User: 'y=f(x) 수식 작성해줘' → write_in_formula_editor('y=f(x)', close_window=True) "
            "- User: '근의 공식 작성' → write_in_formula_editor('x = (-b +- sqrt(b^2 - 4 times a times c)) over (2 times a)', close_window=True) "
            "- User: '이차방정식' → write_in_formula_editor('a times x^2 + b times x + c = 0', close_window=True) ⚠️⚠️⚠️"
            "\n\n**⚠️ CRITICAL: DO NOT USE / CHARACTER! USE 'over' COMMAND!** "
            "\n\n**Korean Formula Editor Syntax Guide (수식 입력기 문법)**: "
            "The formula editor uses English-like commands, NOT math symbols directly. "
            "\n"
            "**Complete Command Reference:** "
            "\n"
            "🚫🚫🚫 OVER - Fractions (분수) - MOST IMPORTANT! 🚫🚫🚫"
            "\n⚠️ THE / CHARACTER IS COMPLETELY FORBIDDEN! USE 'over' COMMAND! ⚠️"
            "\n\n✅ CORRECT SYNTAX:"
            "\n- Simple fraction: a/b → 'a over b' (no grouping needed for simple cases)"
            "\n- Complex fraction: (a+b)/(c+d) → '{a+b} over {c+d}' (use {} for grouping)"
            "\n- With operations: (2*a*b)/(3*c*d) → '{2 times a times b} over {3 times c times d}' "
            "\n- Multiple terms: (a+b+c)/(d+e+f) → '{a+b+c} over {d+e+f}' "
            "\n- Powers: (x^2+1)/(y^3-2) → '{x^2+1} over {y^3-2}' "
            "\n- Nested fractions: (a/b)/(c/d) → '{a over b} over {c over d}' "
            "\n\n❌ WRONG - NEVER DO THIS:"
            "\n- 'a/b' ← NO! Must be 'a over b' "
            "\n- '(x+1)/(y+2)' ← NO! Must be '{x+1} over {y+2}' "
            "\n- 'a÷b' ← NO! Must be 'a over b' "
            "\n- 'sqrt(x+1)' ← NO! Must be 'sqrt {x+1}' - Use {} not ()!"
            "\n- '{x+1}/{y+2}' ← NO! Must be '{x+1} over {y+2}' - Never use / "
            "\n\n📐 GROUPING RULES - CRITICAL:"
            "\n- Format: {numerator} over {denominator} "
            "\n- Use CURLY BRACES {} for ALL grouping - NEVER use parentheses () "
            "\n- Example: '{2 times a} over {3 times b}' ← use {} for grouping! "
            "\n- Inside functions: 'sqrt {x+1}' NOT 'sqrt(x+1)' ← {} everywhere!"
            "\n- Exponents: 'x^2' or 'x^{2}' (both work, but {} is preferred for complex exponents)"
            "\n\n📝 REAL EXAMPLES:"
            "\n- Quadratic formula: 'x = {-b +- sqrt {b^2 - 4 times a times c}} over {2 times a}' ← {} for ALL grouping!"
            "\n- Cubic fraction: '{-b over {3 times a}} over {27 times a^2}' "
            "\n- Simple division: 'd over 54' NOT 'd/54' "
            "\n- Square root: 'sqrt {x^2 + y^2}' NOT 'sqrt(x^2 + y^2)' "
            "\n"
            "TIMES - Multiplication (곱하기): "
            "- a*b → write 'a times b' "
            "\n"
            "ATOP - Stacked without line (위아래): "
            "- Elements stacked vertically → write 'a atop b' "
            "\n"
            "SQRT - Square/nth root (제곱근): "
            "- √x → write 'sqrt x' (simple case, no grouping needed) "
            "- √(x+1) → write 'sqrt {x+1}' ← Use {} for grouping, NOT ()! "
            "- √(b²-4ac) → write 'sqrt {b^2 - 4 times a times c}' ← {} not ()! "
            "- ∛x → write 'sqrt 3 x' "
            "- ⁿ√x → write 'sqrt n x' "
            "\n"
            "^ _ - Superscripts and Subscripts (제곱/아래첨자): "
            "- x² → write 'x^2' or 'x^{2}' (prefer {} for consistency) "
            "- x^(n+1) → write 'x^{n+1}' ← Use {} not ()! "
            "- x₁ → write 'x_1' or 'x_{1}' "
            "- x_(i+1) → write 'x_{i+1}' ← Use {} not ()! "
            "\n"
            "INT, OINT, DINT, TINT, ODINT, OTINT - Integrals (적분): "
            "- ∫ → write 'int' "
            "- ∮ → write 'oint' (closed integral) "
            "- ∫∫ → write 'dint' (double integral) "
            "- ∫∫∫ → write 'tint' (triple integral) "
            "- ∫₀^∞ → write 'int from 0 to infinity' "
            "- ∫ₐ^b → write 'int from a to b' "
            "\n"
            "lim, Lim - Limits (극한): "
            "- lim_{x→0} → write 'lim from x to 0' "
            "- lim_{x→∞} → write 'lim from x to infinity' "
            "\n"
            "SUM, PROD, UNION, INTER - Summation, Product, Set Operations (집합과 합): "
            "- Σ → write 'sum' "
            "- Σᵢ₌₁^n → write 'sum from i=1 to n' "
            "- Π → write 'prod' "
            "- Πᵢ₌₁^n → write 'prod from i=1 to n' "
            "- ⋃ → write 'union' "
            "- ⋂ → write 'inter' "
            "\n"
            "MATRIX, PMATRIX, BMATRIX, DMATRIX - Matrices (행렬): "
            "- Plain matrix → write 'matrix { a # b ## c # d }' "
            "- Parentheses () → write 'pmatrix { a # b ## c # d }' "
            "- Brackets [] → write 'bmatrix { a # b ## c # d }' "
            "- Determinant || → write 'dmatrix { a # b ## c # d }' "
            "- Use # for column separator, ## for row separator "
            "\n"
            "PILE, LPILE, RPILE - Vertical Stack (세로 쌓기): "
            "- Center aligned → write 'pile { a # b # c }' "
            "- Left aligned → write 'lpile { a # b # c }' "
            "- Right aligned → write 'rpile { a # b # c }' "
            "\n"
            "CASES - Piecewise functions (경우들): "
            "- f(x) = { ... → write 'cases { x^2 # x >= 0 ## -x # x < 0 }' "
            "\n"
            "CHOOSE, BINOM - Binomial coefficients (조합): "
            "- (n choose k) → write 'n choose k' or 'binom n k' "
            "\n"
            "BIGG - Large delimiters (가운데 큰 기호): "
            "- Large parentheses → write 'bigg ( ... bigg )' "
            "\n"
            "HAT, CHECK, TILDE, ACUTE, GRAVE, DOT, DDOT, BAR, VEC, DYAD, UNDER - Decorations (글자 꾸밈): "
            "- x̂ → write 'hat x' "
            "- x̌ → write 'check x' "
            "- x̃ → write 'tilde x' "
            "- x́ → write 'acute x' "
            "- x̀ → write 'grave x' "
            "- ẋ → write 'dot x' "
            "- ẍ → write 'ddot x' "
            "- x̄ → write 'bar x' "
            "- →x → write 'vec x' "
            "- x⃡ → write 'dyad x' "
            "- x̲ → write 'under x' "
            "\n"
            "Greek Letters (그리스 문자): "
            "- α → 'alpha', β → 'beta', γ → 'gamma', δ → 'delta' "
            "- ε → 'epsilon', θ → 'theta', λ → 'lambda', μ → 'mu' "
            "- π → 'pi', σ → 'sigma', φ → 'phi', ω → 'omega' "
            "\n"
            "Special Symbols: "
            "- ∞ → 'infinity' "
            "- ≤ → '<=' "
            "- ≥ → '>=' "
            "- ≠ → '!=' "
            "\n"
            "**✅ CORRECT Examples - ALWAYS follow these patterns:** "
            "\n"
            "🔢 Simple fractions:"
            "\n- a/b → write_in_formula_editor('a over b', close_window=True) ✅"
            "\n- 1/2 → write_in_formula_editor('1 over 2', close_window=True) ✅"
            "\n- x/y → write_in_formula_editor('x over y', close_window=True) ✅"
            "\n"
            "🔢 Complex fractions with operations:"
            "\n- (a+b)/(c+d) → write_in_formula_editor('{a+b} over {c+d}', close_window=True) ✅"
            "\n- (2*a)/(3*b) → write_in_formula_editor('{2 times a} over {3 times b}', close_window=True) ✅"
            "\n- d/54 → write_in_formula_editor('d over 54', close_window=True) ✅"
            "\n"
            "🔢 Quadratic formula (근의 공식) - THE MOST IMPORTANT:"
            "\n"
            "\n  📐 Mathematical form: x = [-b ± √(b²-4ac)] / (2a)"
            "\n"
            "\n  📝 Correct structure with CURLY BRACES {} ONLY:"
            "\n     x = {ENTIRE_NUMERATOR} over {ENTIRE_DENOMINATOR}"
            "\n     x = {-b +- sqrt {b^2 - 4 times a times c}} over {2 times a}"
            "\n          └──────────────┬──────────────┘      └─────┬────┘"
            "\n               NUMERATOR (분자)                  DENOMINATOR (분모)"
            "\n"
            "\n  ✅ CORRECT - Use {} for ALL grouping:"
            "\n     write_in_formula_editor('x = {-b +- sqrt {b^2 - 4 times a times c}} over {2 times a}', close_window=True)"
            "\n                                              ↑                          ↑"
            "\n                                          {} inside sqrt!              {} for fraction!"
            "\n"
            "\n  ❌ WRONG - DO NOT use ():"
            "\n     'x = {-b +- sqrt(b^2 - 4 times a times c)} over {2 times a}' ← sqrt(...) is WRONG! Use sqrt {...}"
            "\n     'x = (-b +- sqrt {b^2 - 4 times a times c}) over (2 times a)' ← (...) is WRONG! Use {...}"
            "\n     'x = -b over 2a +- sqrt {...} over 2a' ← NO! This creates TWO separate fractions!"
            "\n     'x = {-b +- sqrt {...}} / {2 times a}' ← NO! Never use / character!"
            "\n"
            "\n  🎯 Key points:"
            "\n     1. Use CURLY BRACES {} for ALL grouping - NEVER parentheses ()"
            "\n     2. sqrt {...} NOT sqrt(...)"
            "\n     3. {...} over {...} for fractions"
            "\n     4. x^{...} NOT x^(...) for exponents"
            "\n"
            "🔢 Cubic formula (3차 방정식 카르다노 공식):"
            "\n- write_in_formula_editor('x = {-b over {3 times a}} + sqrt 3 {...}', close_window=True) ✅"
            "\n- For nested fractions like b/(3a): '{-b over {3 times a}}' ✅ Use {} for grouping!"
            "\n- For fractions like d/54: 'd over 54' NOT 'd/54' ✅"
            "\n"
            "🔢 Other equations:"
            "\n- x²+y² → write_in_formula_editor('x^2+y^2', close_window=True) ✅"
            "\n- E=mc² → write_in_formula_editor('E=m times c^2', close_window=True) ✅"
            "\n"
            "❌ WRONG Examples - NEVER do this:"
            "\n- write_in_formula_editor('a/b', close_window=True) ❌ WRONG!"
            "\n- write_in_formula_editor('d/54', close_window=True) ❌ WRONG!"
            "\n- write_in_formula_editor('{a+b}/{c+d}', close_window=True) ❌ WRONG! Never use /"
            "\n- write_in_formula_editor('(a+b) over (c+d)', close_window=True) ❌ WRONG! Use {} not ()"
            "\n"
            "🔢 More complex examples:"
            "- ∫₀^∞ e^x dx → write_in_formula_editor('int from 0 to infinity e^x dx', close_window=True) "
            "- Σᵢ₌₁^n i → write_in_formula_editor('sum from i=1 to n i', close_window=True) "
            "- 2×2 matrix → write_in_formula_editor('pmatrix { a # b ## c # d }', close_window=True) "
            "- Limit with fraction → write_in_formula_editor('lim from x to 0 {sin x} over x', close_window=True) ✅"
            "- Binomial → write_in_formula_editor('n choose k', close_window=True) "
            "- Decorated x → write_in_formula_editor('hat x', close_window=True) "
            "\n"
            "**CRITICAL RULE for FRACTIONS**: "
            "1. NEVER use the / character in formulas - ALWAYS use 'over' "
            "2. Format: {numerator} over {denominator} - Use CURLY BRACES {} for grouping! "
            "3. Put entire numerator in {}, then 'over', then entire denominator in {} "
            "4. NEVER use parentheses () - ONLY use curly braces {} for ALL grouping "
            "5. sqrt {...} NOT sqrt(...) - Use {} even inside functions "
            "6. x^{...} NOT x^(...) - Use {} for complex exponents "
            "7. WRONG: 'a+b/c+d' or '(a+b)/(c+d)' or '{a+b}/{c+d}' or 'sqrt(x)' or '(a+b) over (c+d)' "
            "8. CORRECT: '{a+b} over {c+d}' and 'sqrt {x+1}' and 'x^{n+1}' "
            "\n"
            "**Process when using write_in_formula_editor(text, close_window=True)**: "
            "1. Open 수식 편집기 window "
            "2. Write the formula in the bottom input area using Korean formula syntax "
            "3. Press Escape to trigger the popup "
            "4. Automatically click the 넣기 button "
            "5. Insert the formula into the document "
            "\n\nFor complex LaTeX formulas (matrices, advanced expressions), use insert_equation(). "
            "For simple formulas and expressions, use write_in_formula_editor() with Korean syntax. "
            "\n\nLaTeX Reference Guide (for insert_equation only):\n"
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
        
        # Build user message with optional image context
        user_message_parts = [f"User request: {description}"]
        
        if image_path:
            user_message_parts.append(
                f"\n\n"
                f"\n🚨🚨🚨 STOP! READ THIS BEFORE GENERATING CODE! 🚨🚨🚨"
                f"\n"
                f"\n❌❌❌ DO NOT WRITE: insert_image()"
                f"\n❌❌❌ DO NOT WRITE: insert_image('/Users/kinn/Downloads/261112.pdf')"
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
                f"\n❌ WRONG CODE EXAMPLES (WILL CRASH):"
                f"\n    insert_image('/Users/...')  # ← CRASH!"
                f"\n    insert_image(image_path)     # ← CRASH!"
                f"\n    insert_picture('/Users/...') # ← CRASH!"
                f"\n"
                f"\n✅ CORRECT CODE EXAMPLES:"
                f"\n    # If image shows: '12. 등비수열 aₙ 이'"
                f"\n    insert_text('12. 등비수열 ')"
                f"\n    write_in_formula_editor('a_n', close_window=True)"
                f"\n    insert_text(' 이')"
                f"\n"
                f"\n    # If image shows a formula: 'x² + y² = z²'"
                f"\n    write_in_formula_editor('x^2 + y^2 = z^2', close_window=True)"
                f"\n"
                f"\n🎯 REMEMBER:"
                f"\n  - You are extracting content FROM the image"
                f"\n  - You are NOT inserting the image file itself"
                f"\n  - insert_image() does not exist in this system"
                f"\n  - Any code with insert_image() will fail"
                f"\n"
            )
        
        if context:
            user_message_parts.append(f"\n\nAdditional context: {context}")
        
        user_message_parts.append(
            "\n\n🚨🚨🚨 FINAL WARNING BEFORE CODE GENERATION 🚨🚨🚨"
            "\n"
            "\nIf this is an image/PDF analysis request:"
            "\n❌ DO NOT generate: insert_image(...)"
            "\n❌ DO NOT generate: insert_picture(...)"
            "\n❌ DO NOT generate: add_image(...)"
            "\n❌ DO NOT include any file path in your code"
            "\n✅ ONLY generate: insert_text() and write_in_formula_editor()"
            "\n"
            "\nGenerate minimal Python code for this request. "
            "In the DESCRIPTION section, write a natural conversational response confirming what you did (not technical explanation). "
            "Follow the format strictly: [DESCRIPTION]...natural response...[/DESCRIPTION] and [CODE]...code...[/CODE]"
        )
        
        user_message = "".join(user_message_parts)

        try:
            if on_thought:
                on_thought("스크립트 생성 중")
            
            print("[ChatGPT] Generating script...")
            
            # Handle image if provided
            image_base64 = None
            if image_path:
                if on_thought:
                    on_thought("이미지 분석 중...")
                print(f"[ChatGPT] Processing image: {image_path}")
                image_base64 = self._encode_image_to_base64(image_path)
                if not image_base64:
                    if on_thought:
                        on_thought("❌ 이미지 처리 실패")
                    print("[ChatGPT] ERROR: Failed to encode image")
                    return None
            
            # Combine system prompt and user message for gpt-5-nano
            full_prompt = f"{system_prompt}\n\n{user_message}"
            generated = self._call_api_with_retry(full_prompt, image_base64=image_base64)
            
            if not generated:
                if on_thought:
                    on_thought(f"❌ 오류 발생: API 응답 없음")
                print("[ChatGPT] ERROR: No response from API")
                return None
            
            # 🚨 CRITICAL: Filter out insert_image() calls if AI generated them anyway
            if image_path and "insert_image(" in generated:
                print("[ChatGPT] ⚠️ WARNING: AI generated insert_image() despite warnings! Filtering it out...")
                import re
                # Remove all insert_image() lines
                lines = generated.split('\n')
                filtered_lines = []
                for line in lines:
                    if 'insert_image(' not in line:
                        filtered_lines.append(line)
                    else:
                        print(f"[ChatGPT] 🚫 Removed line: {line.strip()}")
                generated = '\n'.join(filtered_lines)
            
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
            "\n"
            "✅ AVAILABLE FUNCTIONS:"
            "- insert_text(text: str): Insert text into the document (텍스트) "
            "- insert_paragraph(): Insert a paragraph break "
            "- write_in_formula_editor(text: str, close_window: bool = True): Insert formulas (수식) "
            "- insert_equation(latex: str, font_size_pt: float = 14.0): Insert LaTeX equations (벡터, 행렬, 시그마, 미분, 적분 등) "
            "- insert_hwpeqn(hwpeqn: str, font_size_pt: float = 12.0, eq_font_name: str = 'HYhwpEQ'): Insert HWP equation format "
            "- insert_table(rows: int, cols: int, treat_as_char: bool = False, cell_data: list = None): Insert a table/chart (표). "
            "  Example with data: insert_table(rows=3, cols=2, cell_data=[['Header1', 'Header2'], ['Data1', 'Data2'], ['Data3', 'Data4']]) "
            "\n"
            "🚫 FUNCTIONS THAT DO NOT EXIST:"
            "- insert_image() ← DOES NOT EXIST! Never use this!"
            "\n"
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
