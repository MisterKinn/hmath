# ✅ HWP Startup Check - Feature Added

## What Was Added

The app now **checks if HWP is running when it starts** and shows a friendly reminder dialog if it's not.

## Features

### 1. Startup Check
- When the app launches, it checks if Hancom Office HWP is running (after 500ms delay)
- If HWP is **not running**, shows a friendly information dialog
- Dialog is platform-aware (shows correct app name for Windows vs macOS)

### 2. Visual Status Indicator
- HWP filename pill now shows connection status:
  - **🟢 한글 문서** - HWP is connected ✅
  - **🔴 한글 문서** - HWP is not running ⚠️
- Status updates automatically every 500ms

### 3. Helpful Dialog
When HWP is not running, users see:

```
💡 Hancom Office HWP 프로그램이 실행되지 않았습니다

AI가 문서를 작성하려면 먼저 Hancom Office HWP을(를) 실행해주세요.

1. Hancom Office HWP 실행
2. 문서 열기 또는 새로 만들기
3. 이 앱에서 명령 입력

지금 Hancom Office HWP을(를) 실행하고 문서를 여신 후,
다시 명령을 입력해주세요.
```

## Implementation Details

### New Methods

**`_check_hwp_on_startup()`**
- Called 500ms after app starts
- Attempts to connect to HWP using `HwpController()`
- Shows dialog if connection fails
- Updates status indicator

**`_update_hwp_status_indicator(connected: bool)`**
- Updates the HWP pill with 🟢 or 🔴 indicator
- Preserves existing filename
- Called by startup check and periodic updates

### Modified Methods

**`_update_hwp_filename()`**
- Now checks HWP connection status
- Updates status indicator every 500ms
- Preserves status emoji when updating filename

**`__init__()`**
- Added: `QTimer.singleShot(500, self._check_hwp_on_startup)`
- Triggers startup check after UI loads

## User Experience

### Before
- Users had to try sending a command to discover HWP wasn't running
- Error only appeared after AI generated code
- Confusing "HWP not available" messages

### After
- **Proactive notification** when app starts
- **Real-time status indicator** shows connection state
- **Clear instructions** on how to fix the issue
- Users know immediately if HWP needs to be started

## Platform Support

### macOS
- Detects "Hancom Office HWP" process
- Shows correct app name in dialog
- Uses AppleScript backend for connection check

### Windows
- Detects "HWPFrame.HwpObject" COM object
- Shows "한글(HWP)" in dialog
- Uses win32com backend for connection check

## Benefits

1. **Better UX** - Users know what to do before trying to use the app
2. **Visual Feedback** - Connection status always visible
3. **Reduced Confusion** - Clear instructions instead of errors
4. **Time Saving** - No need to generate code only to find HWP isn't running
5. **Professional Feel** - Proactive checks show polish

## Testing

### Test 1: HWP Running
```bash
# 1. Open Hancom Office HWP with document
# 2. Run app: python3 -m gui.app
# Expected: 🟢 한글 문서 (no dialog)
```

### Test 2: HWP Not Running
```bash
# 1. Close Hancom Office HWP
# 2. Run app: python3 -m gui.app
# Expected: Dialog appears + 🔴 한글 문서
```

### Test 3: Start HWP After App
```bash
# 1. Run app with HWP closed (🔴)
# 2. Dismiss dialog
# 3. Open HWP
# Expected: Indicator changes to 🟢 within 500ms
```

## Code Location

**File:** `gui/main_window.py`

**Lines:**
- `_check_hwp_on_startup()`: ~5989-6061
- `_update_hwp_status_indicator()`: ~6062-6079
- `_update_hwp_filename()`: ~6081-6137 (modified)
- `__init__()`: ~289 (added QTimer call)

## Screenshots

### Dialog (macOS)
```
┌─────────────────────────────────────────┐
│ HWP 실행 안내                        [X] │
├─────────────────────────────────────────┤
│ 💡 Hancom Office HWP 프로그램이         │
│    실행되지 않았습니다                    │
│                                         │
│ AI가 문서를 작성하려면 먼저             │
│ Hancom Office HWP을(를) 실행해주세요.   │
│                                         │
│ 1. Hancom Office HWP 실행               │
│ 2. 문서 열기 또는 새로 만들기            │
│ 3. 이 앱에서 명령 입력                   │
│                                         │
│               [ 확인 ]                   │
└─────────────────────────────────────────┘
```

### Status Indicators
```
Connected:     🟢 한글 문서
Disconnected:  🔴 한글 문서
```

## Future Enhancements

- [ ] Add "Open HWP" button in dialog (auto-launch)
- [ ] Show last connection time
- [ ] Add retry button in dialog
- [ ] Show more detailed error messages
- [ ] Add option to disable startup check

---

**Status:** ✅ Complete and Working
**Date:** Dec 27, 2024
**Version:** 1.1.0-macos


