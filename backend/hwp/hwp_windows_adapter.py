"""Windows HWP Detection Adapter - Uses COM automation to detect active HWP document."""

from __future__ import annotations

import logging
from typing import Dict, Optional, Any
from pathlib import Path


logger = logging.getLogger(__name__)


class WindowsHwpAdapter:
    """Windows adapter for HWP filename detection using COM automation."""
    
    def __init__(self):
        self._last_result: Optional[Dict[str, Any]] = None
        self._com_available = False
        
        # Try to import COM libraries
        try:
            import win32com.client  # type: ignore
            self._com_available = True
            logger.debug("[WindowsHwpAdapter] COM libraries available")
        except ImportError:
            logger.debug("[WindowsHwpAdapter] COM libraries not available")
    
    def get_hwp_filename(self) -> Dict[str, Any]:
        """
        Get current HWP filename using COM automation.
        
        Returns:
            Dictionary with structure:
            {
                "success": bool,
                "filename": str | None,
                "error": str | None
            }
        """
        if not self._com_available:
            return {
                "success": False,
                "filename": None,
                "error": "COM libraries not available (install pywin32)"
            }
        
        try:
            import win32com.client  # type: ignore
            
            logger.debug("[WindowsHwpAdapter] Attempting COM connection")
            
            # Connect to HWP application
            hwp = win32com.client.Dispatch("HWPFrame.HwpObject")
            
            if not hwp:
                return {
                    "success": False,
                    "filename": None,
                    "error": "Could not connect to HWP application"
                }
            
            # Get document path
            doc_path = hwp.Path
            
            if not doc_path:
                # No document open or unsaved document
                return {
                    "success": True,
                    "filename": None,
                    "error": None
                }
            
            # Extract filename from path
            filename = Path(doc_path).name
            normalized_filename = self._normalize_filename(filename)
            
            logger.debug(f"[WindowsHwpAdapter] Found filename: '{normalized_filename}'")
            
            return {
                "success": True,
                "filename": normalized_filename,
                "error": None
            }
            
        except Exception as e:
            error_msg = f"COM error: {type(e).__name__}: {str(e)}"
            logger.warning(f"[WindowsHwpAdapter] {error_msg}")
            return {
                "success": False,
                "filename": None,
                "error": error_msg
            }
    
    def _normalize_filename(self, filename: str) -> Optional[str]:
        """
        Normalize filename from COM result.
        
        Args:
            filename: Raw filename from COM
            
        Returns:
            Normalized filename or None if invalid
        """
        if not filename:
            return None
        
        # Strip whitespace
        filename = filename.strip()
        
        if not filename:
            return None
        
        # Check for invalid filenames
        invalid_names = {"", "한글 문서"}
        if filename in invalid_names:
            return None
        
        return filename if filename else None
    
    def is_available(self) -> bool:
        """Check if the adapter can be used on this system."""
        if not self._com_available:
            return False
        
        try:
            import win32com.client  # type: ignore
            # Try a quick connection test
            hwp = win32com.client.Dispatch("HWPFrame.HwpObject")
            return hwp is not None
        except Exception:
            return False