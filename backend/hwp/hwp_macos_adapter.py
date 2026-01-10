"""macOS HWP Detection Adapter - Uses AppleScript to detect active HWP document."""

from __future__ import annotations

import subprocess
import logging
from typing import Dict, Optional, Any
from pathlib import Path


logger = logging.getLogger(__name__)


class MacOSHwpAdapter:
    """macOS adapter for HWP filename detection using AppleScript."""
    
    # Exact AppleScript as specified in requirements
    APPLESCRIPT = '''
tell application "System Events"
    tell application process "Hancom Office HWP"
        if (count of windows) > 0 then
            return name of front window
        else
            return ""
        end if
    end tell
end tell
'''
    
    def __init__(self):
        self._last_result: Optional[Dict[str, Any]] = None
    
    def get_hwp_filename(self) -> Dict[str, Any]:
        """
        Get current HWP filename using AppleScript.
        
        Returns:
            Dictionary with structure:
            {
                "success": bool,
                "filename": str | None,
                "error": str | None
            }
        """
        try:
            logger.debug("[MacOSHwpAdapter] Executing osascript")
            
            # Execute osascript with the exact AppleScript
            result = subprocess.run(
                ['osascript', '-e', self.APPLESCRIPT],
                capture_output=True,
                text=True,
                timeout=5.0  # 5 second timeout
            )
            
            logger.debug(f"[MacOSHwpAdapter] osascript returncode: {result.returncode}")
            logger.debug(f"[MacOSHwpAdapter] osascript stdout: '{result.stdout}'")
            if result.stderr:
                logger.debug(f"[MacOSHwpAdapter] osascript stderr: '{result.stderr}'")
            
            if result.returncode != 0:
                error_msg = f"osascript failed with code {result.returncode}"
                if result.stderr:
                    error_msg += f": {result.stderr.strip()}"
                
                logger.warning(f"[MacOSHwpAdapter] {error_msg}")
                return {
                    "success": False,
                    "filename": None,
                    "error": error_msg
                }
            
            # Process output
            raw_output = result.stdout
            normalized_filename = self._normalize_output(raw_output)
            
            logger.debug(f"[MacOSHwpAdapter] Normalized filename: '{normalized_filename}'")
            
            return {
                "success": True,
                "filename": normalized_filename,
                "error": None
            }
            
        except subprocess.TimeoutExpired:
            error_msg = "osascript timeout (5s)"
            logger.warning(f"[MacOSHwpAdapter] {error_msg}")
            return {
                "success": False,
                "filename": None,
                "error": error_msg
            }
        except FileNotFoundError:
            error_msg = "osascript not found (not macOS?)"
            logger.warning(f"[MacOSHwpAdapter] {error_msg}")
            return {
                "success": False,
                "filename": None,
                "error": error_msg
            }
        except Exception as e:
            error_msg = f"Unexpected error: {type(e).__name__}: {str(e)}"
            logger.error(f"[MacOSHwpAdapter] {error_msg}")
            return {
                "success": False,
                "filename": None,
                "error": error_msg
            }
    
    def _normalize_output(self, raw_output: str) -> Optional[str]:
        """
        Normalize osascript output according to spec.
        
        Args:
            raw_output: Raw stdout from osascript
            
        Returns:
            Normalized filename or None if invalid
        """
        if not raw_output:
            return None
        
        # Strip whitespace
        filename = raw_output.strip()
        
        if not filename:
            return None
        
        # Remove " - 한글" suffix if present
        if filename.endswith(" - 한글"):
            filename = filename[:-5].strip()
        
        # Check for invalid filenames
        invalid_names = {"", "한글 문서"}
        if filename in invalid_names:
            return None
        
        return filename if filename else None
    
    def is_available(self) -> bool:
        """Check if the adapter can be used on this system."""
        try:
            # Quick test to see if osascript is available
            result = subprocess.run(
                ['osascript', '-e', 'return "test"'],
                capture_output=True,
                text=True,
                timeout=2.0
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired, Exception):
            return False