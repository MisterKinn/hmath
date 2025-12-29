# 🔧 Bug Fix: macOS Recognition Issue

## Issue
The app was not recognizing 한글 program on macOS even though it was running.

## Root Cause
In `gui/main_window.py` line 5148-5150, the HWP availability check was using Windows-only code:

```python
import win32com.client  # Windows-only!
hwp = win32com.client.gencache.EnsureDispatch("HWPFrame.HwpObject")
```

This would **always fail on macOS**, causing the app to think HWP is not available.

## Fix Applied
Replaced Windows-specific check with cross-platform check:

```python
test_hwp = HwpController()  # Works on both Windows and macOS!
test_hwp.connect()
```

The `HwpController` automatically detects the platform and uses:
- **Windows:** `win32com.client` + `pyhwpx`
- **macOS:** AppleScript automation

## Files Modified
- `gui/main_window.py` (line ~5146-5152)
- `backend/hwp/hwp_macos.py` (app name order)

## Test Results
✅ HWP detection now working on macOS:
```bash
$ python3 -c "from backend.hwp.hwp_controller import HwpController; test_hwp = HwpController(); test_hwp.connect(); print('✅ HWP is available!')"
✅ HWP is available!
```

## What This Fixes
1. ✅ AI can now detect when Hancom Office HWP is running on macOS
2. ✅ Auto-execution mode works (AI generates code → executes on HWP)
3. ✅ Error messages show correctly when HWP is not available
4. ✅ No more "한글(HWP)이 실행 중이지 않아..." false positives

## How to Verify
```bash
# 1. Open Hancom Office HWP with a document
# 2. Run the app
python3 -m gui.app

# 3. Type: "안녕하세요를 입력해줘"
# 4. Press Enter
# 5. Check HWP document - text should appear!
```

## Status
🎉 **FIXED!** The app now correctly recognizes Hancom Office HWP on macOS.

---

Date: Dec 27, 2024
Version: 1.0.1-macos



