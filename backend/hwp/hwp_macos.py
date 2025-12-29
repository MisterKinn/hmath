"""
macOS AppleScript-based control for 한글 (Hancom Hangul).
"""

import subprocess
import logging
from typing import Optional

from backend.math_unicode_converter import latex_to_unicode

logger = logging.getLogger(__name__)


class HwpMacOSError(RuntimeError):
    """Base exception for macOS HWP automation failures."""
    pass


class HwpMacOS:
    """
    macOS-specific HWP controller using AppleScript automation.
    """

    def __init__(self):
        # Try different possible app names (macOS specific)
        self._possible_names = [
            "Hancom Office HWP",      # Official macOS app name
            "Hancom Office Hangul",
            "한글",
            "Hangul",
            "HWP",
            "한글과컴퓨터 오피스 한글"
        ]
        self._app_name = None
        self._detect_app_name()
        
    def _detect_app_name(self) -> None:
        """Detect which variation of the app name is correct."""
        for name in self._possible_names:
            if self._check_app_exists(name):
                self._app_name = name
                logger.info(f"Detected 한글 app name: {name}")
                return
        
        # Default to first option if none found
        self._app_name = self._possible_names[0]
        logger.warning(f"Could not detect 한글 app, defaulting to: {self._app_name}")
    
    def _check_app_exists(self, app_name: str) -> bool:
        """Check if an app with given name is installed."""
        script = f'''
        try
            tell application "{app_name}"
                return true
            end tell
        on error
            return false
        end try
        '''
        try:
            result = self._run_applescript(script, check_error=False)
            return result.strip().lower() == "true"
        except Exception:
            return False
        
    def is_running(self) -> bool:
        """Check if 한글 application is running."""
        if not self._app_name:
            return False
            
        script = f'''
        tell application "System Events"
            return (name of processes) contains "{self._app_name}"
        end tell
        '''
        try:
            result = self._run_applescript(script, check_error=False)
            return result.strip().lower() == "true"
        except Exception:
            return False
    
    def activate(self) -> None:
        """Bring 한글 to the front."""
        script = f'''
        tell application "{self._app_name}"
            activate
        end tell
        '''
        try:
            self._run_applescript(script)
        except Exception as exc:
            raise HwpMacOSError(f"Failed to activate 한글: {exc}") from exc
    
    def insert_text(self, text: str) -> None:
        """
        Insert text into the active 한글 document using clipboard.
        
        Note: Using clipboard is more reliable than keystroke for Korean text.
        The app must be frontmost and a document must be open.
        """
        if not text:
            return
        
        # Use pbcopy for robust clipboard handling (avoids AppleScript escaping issues)
        try:
            # Copy text to clipboard using pbcopy
            subprocess.run(
                ['pbcopy'],
                input=text.encode('utf-8'),
                check=True,
                timeout=2
            )
            
            # Paste using Command+V and handle "골라 붙이기" (Paste Special) dialog
            paste_script = f'''
            tell application "{self._app_name}"
                activate
            end tell
            
            delay 0.1
            
            tell application "System Events"
                tell process "{self._app_name}"
                    -- Paste with Command+V
                    keystroke "v" using command down
                    delay 0.5
                    
                    -- Handle "골라 붙이기" (Paste Special) dialog
                    -- Press Enter to confirm the dialog (clicks "붙이기" button)
                    -- Note: If dialog doesn't appear, Enter might add a newline
                    -- but this is acceptable to ensure dialog is handled
                    try
                        -- Check if dialog window exists
                        set hasDialog to false
                        try
                            repeat with w in windows
                                try
                                    if (title of w as string) contains "골라 붙이기" then
                                        set hasDialog to true
                                        exit repeat
                                    end if
                                end try
                            end repeat
                        end try
                        
                        -- Press Enter to confirm dialog (or add newline if no dialog)
                        -- This ensures dialog is always handled
                        key code 36  -- Enter key
                        delay 0.2
                        
                        -- If no dialog was detected but we pressed Enter,
                        -- remove the extra newline
                        if not hasDialog then
                            key code 51  -- Backspace to remove newline
                            delay 0.1
                        end if
                    on error
                        -- Fallback: press Enter to handle dialog
                        key code 36
                        delay 0.1
                    end try
                end tell
            end tell
            '''
            
            self._run_applescript(paste_script)
            logger.info(f"Inserted text via clipboard: {text[:50]}...")
            
        except subprocess.TimeoutExpired:
            raise HwpMacOSError("Clipboard copy timed out")
        except Exception as exc:
            raise HwpMacOSError(f"Failed to insert text: {exc}") from exc
    
    def insert_math_text(self, latex_text: str) -> None:
        """
        Insert math formula by converting LaTeX to Unicode.
        
        Converts LaTeX notation to Unicode math symbols that display correctly.
        Example: "x^2 + y^2 = z^2" → "x² + y² = z²"
        """
        unicode_text = latex_to_unicode(latex_text)
        self.insert_text(unicode_text)
    
    def open_formula_editor(self) -> None:
        """
        Open the 수식 편집기 (Formula Editor) window using menu navigation.
        
        This opens the formula editor window where you can manually type formulas.
        Uses menu path: 입력  (Input with trailing space) → 수식... (Equation with ellipsis)
        """
        try:
            self.activate()
            delay = 0.3
            
            script = f'''
            tell application "{self._app_name}"
                activate
            end tell
            
            delay {delay}
            
            tell application "System Events"
                tell process "{self._app_name}"
                    set lastError to ""
                    -- Try to open formula editor via menu
                    -- Path: 입력  (with trailing space) → 수식... (with ellipsis)
                    try
                        -- Method 1: Try Korean menu "입력 " (with trailing space) → "수식..."
                        click menu item "수식..." of menu "입력 " of menu bar 1
                        return "SUCCESS: 입력  → 수식..."
                    on error err1
                        set lastError to err1
                        try
                            -- Method 2: Try "입력" (without space) → "수식..."
                            click menu item "수식..." of menu "입력" of menu bar 1
                            return "SUCCESS: 입력 → 수식..."
                        on error err2
                            set lastError to err2
                            try
                                -- Method 3: Try "입력 " → "수식" (without ellipsis)
                                click menu item "수식" of menu "입력 " of menu bar 1
                                return "SUCCESS: 입력  → 수식"
                            on error err3
                                set lastError to err3
                                try
                                    -- Method 4: Try "삽입" → "수식..."
                                    click menu item "수식..." of menu "삽입" of menu bar 1
                                    return "SUCCESS: 삽입 → 수식..."
                                on error err4
                                    set lastError to err4
                                    try
                                        -- Method 5: Try "삽입" → "수식"
                                        click menu item "수식" of menu "삽입" of menu bar 1
                                        return "SUCCESS: 삽입 → 수식"
                                    on error err5
                                        set lastError to err5
                                        try
                                            -- Method 6: Try English menu "Input" → "Equation..."
                                            click menu item "Equation..." of menu "Input" of menu bar 1
                                            return "SUCCESS: Input → Equation..."
                                        on error err6
                                            set lastError to err6
                                            try
                                                -- Method 7: Try keyboard shortcut Option+Command+E
                                                keystroke "e" using {{option down, command down}}
                                                return "SUCCESS: Option+Command+E"
                                            on error err7
                                                set lastError to err7
                                                return "FAILED: All methods failed. Last error: " & lastError
                                            end try
                                        end try
                                    end try
                                end try
                            end try
                        end try
                    end try
                end tell
            end tell
            '''
            
            result = self._run_applescript(script)
            if result and "SUCCESS" in result:
                logger.info(f"Opened formula editor: {result.strip()}")
            else:
                logger.warning("Formula editor opened but no success message returned")
            logger.info("Opened formula editor window")
            
        except Exception as exc:
            error_msg = str(exc)
            logger.error(f"Failed to open formula editor: {error_msg}")
            raise HwpMacOSError(
                f"수식 편집기를 열 수 없습니다.\n"
                f"한글 앱의 메뉴 구조가 다를 수 있습니다.\n"
                f"수동으로 '입력 → 수식...' 메뉴를 확인해주세요.\n"
                f"오류: {error_msg}"
            ) from exc
    
    def type_in_open_formula_editor(self, text: str, close_window: bool = False) -> None:
        """
        Type text in an ALREADY OPEN 수식 편집기 (Formula Editor) window.
        
        This assumes the formula editor window is already open.
        Use open_formula_editor() first to open the window.
        
        Args:
            text: Plain text to type (can be formula syntax or regular text)
            close_window: If True, closes window with Escape and clicks "넣기" button
        """
        try:
            # Escape special characters for AppleScript
            escaped_text = text.replace('\\', '\\\\').replace('"', '\\"')
            
            # Build close command with popup handling
            close_commands = ""
            if close_window:
                close_commands = '''
                    -- Close window with Escape
                    key code 53
                    delay 1.0
                    
                    -- Click "넣기" button in popup
                    try
                        click button "넣기" of window 1
                        delay 0.3
                    on error
                        -- If popup doesn't appear or button not found, just continue
                        delay 0.1
                    end try
'''
            
            script = f'''
            tell application "{self._app_name}"
                activate
            end tell
            
            delay 0.3
            
            tell application "System Events"
                tell process "{self._app_name}"
                    -- Find and focus on the scroll area (bottom black input area)
                    set formulaWindow to window "수식 편집기"
                    
                    repeat with elem in (UI elements of formulaWindow)
                        if role of elem is "AXScrollArea" then
                            -- Focus on the scroll area (bottom input area)
                            set focused of elem to true
                            delay 0.3
                            
                            -- Type text in the bottom input area
                            keystroke "{escaped_text}"
                            delay 0.5
                            {close_commands}
                            return "SUCCESS: Typed and inserted"
                        end if
                    end repeat
                    
                    return "ERROR: Bottom input area not found"
                end tell
            end tell
            '''
            
            result = self._run_applescript(script)
            
            if result and "SUCCESS" in result:
                action = "inserted" if close_window else "typed"
                logger.info(f"Text {action} in formula editor: {text[:50]}...")
            else:
                logger.warning(f"Formula editor result: {result.strip()}")
            
        except Exception as exc:
            raise HwpMacOSError(f"Failed to type in formula editor: {exc}") from exc
    
    def write_in_formula_editor(self, text: str, close_window: bool = False) -> None:
        """
        Complete process: Open formula editor window and type text.
        
        Process:
        1. Open the 수식 편집기 window
        2. Wait for window to open
        3. Type text in the bottom black input area
        
        Args:
            text: Plain text to type (can be formula syntax or regular text)
            close_window: If True, closes window with Escape to insert into document
        """
        try:
            # Step 1: Open formula editor
            logger.info("Step 1: Opening formula editor window...")
            self.open_formula_editor()
            
            # Step 2: Wait for window to fully open
            import time
            time.sleep(1.5)
            logger.info("Step 2: Window opened, ready to type...")
            
            # Step 3: Type text in the open window
            logger.info(f"Step 3: Typing text: {text[:50]}...")
            self.type_in_open_formula_editor(text, close_window)
            
        except Exception as exc:
            raise HwpMacOSError(f"Failed to write in formula editor: {exc}") from exc
    
    def insert_equation_via_editor(self, formula_text: str) -> None:
        """
        Insert equation using the 수식 편집기 (Formula Editor) window in 한글.
        
        Opens the formula editor window, enters the formula, and automatically clicks "넣기".
        The formula_text should be in 한글 수식 편집기 format (e.g., "a over b" for fractions).
        
        Args:
            formula_text: Formula in 한글 formula editor syntax
        """
        try:
            # Use the new 3-step process
            # This ensures we use the correct input area (bottom black area, not font size field)
            self.write_in_formula_editor(formula_text, close_window=True)
            
        except Exception as exc:
            raise HwpMacOSError(f"Failed to insert equation via editor: {exc}") from exc
    
    def insert_paragraph_break(self) -> None:
        """Insert a new paragraph (Enter key)."""
        script = f'''
        tell application "{self._app_name}"
            activate
        end tell
        
        tell application "System Events"
            tell process "{self._app_name}"
                key code 36
            end tell
        end tell
        '''
        
        try:
            self._run_applescript(script)
        except Exception as exc:
            raise HwpMacOSError(f"Failed to insert paragraph break: {exc}") from exc
    
    def _run_applescript(self, script: str, check_error: bool = True) -> str:
        """Execute AppleScript and return output."""
        try:
            result = subprocess.run(
                ['osascript', '-e', script],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if check_error and result.returncode != 0:
                error_msg = result.stderr
                
                # Check for accessibility permission error
                if "osascript is not allowed to send keystrokes" in error_msg or "1002" in error_msg:
                    raise HwpMacOSError(
                        "❌ Accessibility permissions not granted!\n\n"
                        "To fix this:\n"
                        "1. Open System Settings (시스템 설정)\n"
                        "2. Go to Privacy & Security (개인 정보 보호 및 보안)\n"
                        "3. Click Accessibility (손쉬운 사용)\n"
                        "4. Click the + button and add Terminal (or your terminal app)\n"
                        "5. Enable the toggle\n"
                        "6. Restart Terminal and try again\n"
                    )
                
                raise HwpMacOSError(f"AppleScript error: {error_msg}")
            
            return result.stdout
        except subprocess.TimeoutExpired:
            raise HwpMacOSError("AppleScript execution timed out")
        except HwpMacOSError:
            # Re-raise our custom errors
            raise
        except Exception as exc:
            if check_error:
                raise HwpMacOSError(f"Failed to run AppleScript: {exc}") from exc
            return ""

