"""HWP Detector - Cross-platform HWP filename detection with polling logic."""

from __future__ import annotations

import platform
import logging
from typing import Optional, Dict, Any
from PySide6.QtCore import QTimer, QObject, Signal

from .hwp_state_manager import HwpStateManager, HwpState
from .hwp_macos_adapter import MacOSHwpAdapter
from .hwp_windows_adapter import WindowsHwpAdapter


logger = logging.getLogger(__name__)


class HwpDetector(QObject):
    """Cross-platform HWP filename detector with polling and state management."""
    
    # Signal emitted when HWP state changes
    state_changed = Signal(object)  # HwpState object
    
    def __init__(self, poll_interval_ms: int = 500):
        """
        Initialize HWP detector.
        
        Args:
            poll_interval_ms: Polling interval in milliseconds (300-1000ms as per spec)
        """
        super().__init__()
        
        self._poll_interval = max(300, min(1000, poll_interval_ms))
        self._state_manager = HwpStateManager()
        self._adapter: Optional[MacOSHwpAdapter | WindowsHwpAdapter] = None
        self._timer = QTimer()
        self._running = False
        
        # Set up timer
        self._timer.timeout.connect(self._poll_hwp_state)
        self._timer.setSingleShot(False)
        
        # Connect state manager to our signal
        self._state_manager.add_listener(self._on_state_changed)
        
        # Initialize adapter based on platform
        self._initialize_adapter()
        
        logger.info(f"[HwpDetector] Initialized with {self._poll_interval}ms polling interval")
    
    def _initialize_adapter(self) -> None:
        """Initialize the appropriate adapter based on platform."""
        system = platform.system().lower()
        
        if system == "darwin":  # macOS
            adapter = MacOSHwpAdapter()
            if adapter.is_available():
                self._adapter = adapter
                logger.info("[HwpDetector] Using macOS adapter")
            else:
                logger.warning("[HwpDetector] macOS adapter not available")
        elif system == "windows":
            adapter = WindowsHwpAdapter()
            if adapter.is_available():
                self._adapter = adapter
                logger.info("[HwpDetector] Using Windows adapter")
            else:
                logger.warning("[HwpDetector] Windows adapter not available")
        else:
            logger.warning(f"[HwpDetector] Unsupported platform: {system}")
        
        if not self._adapter:
            logger.warning("[HwpDetector] No suitable adapter available")
    
    def start_polling(self) -> bool:
        """
        Start polling for HWP state changes.
        
        Returns:
            True if polling started successfully
        """
        if not self._adapter:
            logger.error("[HwpDetector] Cannot start polling: no adapter available")
            return False
        
        if self._running:
            logger.debug("[HwpDetector] Polling already running")
            return True
        
        self._running = True
        self._timer.start(self._poll_interval)
        logger.info(f"[HwpDetector] Started polling every {self._poll_interval}ms")
        
        # Do initial poll
        self._poll_hwp_state()
        
        return True
    
    def stop_polling(self) -> None:
        """Stop polling for HWP state changes."""
        if not self._running:
            return
        
        self._running = False
        self._timer.stop()
        logger.info("[HwpDetector] Stopped polling")
    
    def _poll_hwp_state(self) -> None:
        """Poll HWP state and update state manager if changed."""
        if not self._adapter:
            return
        
        try:
            logger.debug("[HwpDetector] Polling HWP state")
            
            # Get current state from adapter
            result = self._adapter.get_hwp_filename()
            
            if result["success"]:
                filename = result["filename"]
                is_running = True  # If we got a successful result, HWP is running
                
                logger.debug(f"[HwpDetector] Poll result: running={is_running}, filename='{filename}'")
                
                # Update state manager (will notify if changed)
                changed = self._state_manager.update_state(
                    filename=filename,
                    is_running=is_running
                )
                
                if changed:
                    logger.info(f"[HwpDetector] State changed: {self._state_manager.get_display_filename()}")
            else:
                # Error or HWP not running
                error = result.get("error", "Unknown error")
                
                # Determine if this is a "not running" vs "error" case
                is_running = False
                if "not found" in error.lower() or "timeout" in error.lower():
                    is_running = False
                else:
                    # Other errors might indicate HWP is running but we can't access it
                    # For now, treat as not running
                    is_running = False
                
                logger.debug(f"[HwpDetector] Poll failed: {error}")
                
                # Update state (HWP not running or error accessing it)
                changed = self._state_manager.update_state(
                    filename=None,
                    is_running=is_running
                )
                
                if changed:
                    logger.info(f"[HwpDetector] State changed: {self._state_manager.get_display_filename()}")
        
        except Exception as e:
            logger.error(f"[HwpDetector] Error during polling: {type(e).__name__}: {e}")
            
            # On unexpected error, assume HWP not running
            self._state_manager.update_state(
                filename=None,
                is_running=False
            )
    
    def _on_state_changed(self, state: HwpState) -> None:
        """Handle state change from state manager."""
        logger.debug(f"[HwpDetector] Emitting state_changed signal")
        self.state_changed.emit(state)
    
    def get_current_state(self) -> HwpState:
        """Get current HWP state."""
        return self._state_manager.get_state()
    
    def get_display_filename(self) -> str:
        """Get filename for UI display."""
        return self._state_manager.get_display_filename()
    
    def is_adapter_available(self) -> bool:
        """Check if an adapter is available for the current platform."""
        return self._adapter is not None
    
    def force_update(self) -> None:
        """Force an immediate poll and state update."""
        if self._running:
            self._poll_hwp_state()