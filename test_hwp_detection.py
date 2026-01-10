#!/usr/bin/env python3
"""
Test script for HWP filename detection feature.

This script demonstrates the cross-platform HWP detection system
that monitors the active HWP document filename in real-time.
"""

import sys
import time
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

from backend.hwp.hwp_detector import HwpDetector


def test_hwp_detection():
    """Test the HWP detection system."""
    print("🔍 Testing HWP Detection System")
    print("=" * 50)
    
    # Create detector
    detector = HwpDetector(poll_interval_ms=1000)  # 1 second polling for demo
    
    # Check if adapter is available
    if not detector.is_adapter_available():
        print("❌ No HWP adapter available on this platform")
        return
    
    print("✅ HWP adapter available")
    
    # Set up state change handler
    def on_state_change(state):
        print(f"📄 HWP State Changed:")
        print(f"   Running: {state.is_hwp_running}")
        print(f"   Filename: {state.current_hwp_filename}")
        print(f"   Display: {detector.get_display_filename()}")
        print(f"   Last Valid: {state.last_valid_hwp_filename}")
        print(f"   Timestamp: {state.last_update_timestamp}")
        print("-" * 30)
    
    detector.state_changed.connect(on_state_change)
    
    # Start polling
    print("🚀 Starting HWP detection...")
    if detector.start_polling():
        print("✅ Polling started successfully")
    else:
        print("❌ Failed to start polling")
        return
    
    # Show initial state
    initial_state = detector.get_current_state()
    print(f"📊 Initial State: {detector.get_display_filename()}")
    
    try:
        print("\n🔄 Monitoring HWP state changes...")
        print("   (Open/close HWP documents to see real-time updates)")
        print("   Press Ctrl+C to stop")
        
        # Monitor for 30 seconds
        for i in range(30):
            time.sleep(1)
            if i % 5 == 0:
                print(f"⏱️  Monitoring... ({30-i}s remaining)")
    
    except KeyboardInterrupt:
        print("\n⏹️  Monitoring stopped by user")
    
    finally:
        # Stop polling
        detector.stop_polling()
        print("🛑 HWP detection stopped")


if __name__ == "__main__":
    test_hwp_detection()