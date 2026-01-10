"""HWP State Manager - Central state management for HWP filename tracking."""

from __future__ import annotations

import time
from typing import Optional, Dict, Any, Callable
from dataclasses import dataclass


@dataclass
class HwpState:
    """HWP application state."""
    current_hwp_filename: Optional[str] = None
    last_valid_hwp_filename: Optional[str] = None
    is_hwp_running: bool = False
    last_update_timestamp: float = 0.0


class HwpStateManager:
    """Central state manager for HWP filename tracking with diff-based updates."""
    
    def __init__(self):
        self._state = HwpState()
        self._listeners: list[Callable[[HwpState], None]] = []
    
    def get_state(self) -> HwpState:
        """Get current HWP state."""
        return self._state
    
    def add_listener(self, callback: Callable[[HwpState], None]) -> None:
        """Add a state change listener."""
        if callback not in self._listeners:
            self._listeners.append(callback)
    
    def remove_listener(self, callback: Callable[[HwpState], None]) -> None:
        """Remove a state change listener."""
        if callback in self._listeners:
            self._listeners.remove(callback)
    
    def update_state(
        self,
        filename: Optional[str] = None,
        is_running: bool = False,
        force_notify: bool = False
    ) -> bool:
        """
        Update HWP state with diff-based change detection.
        
        Args:
            filename: Current HWP filename (None if no document open)
            is_running: Whether HWP is currently running
            force_notify: Force notification even if no changes detected
            
        Returns:
            True if state changed and listeners were notified
        """
        old_state = HwpState(
            current_hwp_filename=self._state.current_hwp_filename,
            last_valid_hwp_filename=self._state.last_valid_hwp_filename,
            is_hwp_running=self._state.is_hwp_running,
            last_update_timestamp=self._state.last_update_timestamp
        )
        
        # Update state
        self._state.is_hwp_running = is_running
        self._state.current_hwp_filename = filename
        self._state.last_update_timestamp = time.time()
        
        # Update last valid filename if we have a valid one
        if filename and self._is_valid_filename(filename):
            self._state.last_valid_hwp_filename = filename
        
        # Check if state changed
        state_changed = (
            old_state.current_hwp_filename != self._state.current_hwp_filename or
            old_state.is_hwp_running != self._state.is_hwp_running or
            force_notify
        )
        
        if state_changed:
            self._notify_listeners()
            return True
        
        return False
    
    def _is_valid_filename(self, filename: str) -> bool:
        """Check if filename is valid (not empty, not default placeholder)."""
        if not filename or not filename.strip():
            return False
        
        # Invalid filenames as per spec
        invalid_names = {"", "한글 문서"}
        return filename.strip() not in invalid_names
    
    def _notify_listeners(self) -> None:
        """Notify all registered listeners of state change."""
        for callback in self._listeners[:]:  # Copy list to avoid modification during iteration
            try:
                callback(self._state)
            except Exception as e:
                print(f"[HwpStateManager] Error in listener callback: {e}")
    
    def get_display_filename(self) -> str:
        """
        Get filename for UI display with fallback logic.
        
        Returns appropriate display text based on current state.
        """
        if not self._state.is_hwp_running:
            return "HWP not running"
        
        if self._state.current_hwp_filename and self._is_valid_filename(self._state.current_hwp_filename):
            return self._state.current_hwp_filename
        
        if self._state.current_hwp_filename:
            return "Untitled HWP document"
        
        return "HWP not running"