# 🚀 macOS Quick Start

## ⚠️ FIRST TIME ONLY: Grant Accessibility Permissions

**IMPORTANT:** Before using the app, you MUST grant accessibility permissions to Terminal!

### Quick Setup:
1. Open **System Settings** → **Privacy & Security** → **Accessibility**
2. Click **+** and add **Terminal** (or your terminal app)
3. Enable the toggle ✅
4. Restart Terminal

**Detailed guide:** See [ACCESSIBILITY_PERMISSIONS.md](ACCESSIBILITY_PERMISSIONS.md)

---

## One-Time Setup
```bash
cd /Users/kinn/Desktop/formulite
pip3 install -r requirements.txt
```

## Every Time You Use The App

### Step 1: Open Hancom Office HWP
- Launch **Hancom Office HWP** (not "한글" - use the full app name)
- Create new document **OR** open existing document
- Keep it open (can be in background)

### Step 2: Check System
```bash
python3 check_macos.py
```
Should see: `✅ All checks passed!`

### Step 3: Run App
```bash
./start_macos.sh
```
Or:
```bash
python3 -m gui.app
```

### Step 4: Use It!
Type commands like:
- "안녕하세요를 입력해줘"
- "오늘의 날짜를 적어줘"
- "테이블을 만들어줘"

Press **Enter** to send.

---

## Troubleshooting

### ❌ "osascript is not allowed to send keystrokes"
**Fix:** Grant Accessibility permissions! See [ACCESSIBILITY_PERMISSIONS.md](ACCESSIBILITY_PERMISSIONS.md)

### ❌ "한글이 실행 중이지 않습니다"
**Fix:** 
1. Open **Hancom Office HWP** (not just "한글")
2. Make sure a document is open
3. Try again

### ❌ "AppleScript error"
**Fix:** 
1. Restart Terminal completely (quit and reopen)
2. Make sure accessibility permissions are enabled
3. Try adding Python.app to Accessibility list too

### ❌ "No module named..."
**Fix:** `pip3 install -r requirements.txt`

---

## Keyboard Shortcuts
- **Enter** - Send message to AI
- **Shift+Enter** - New line in input
- **⌘Q** - Quit app

---

That's it! Enjoy your AI-powered HWP automation! 🎉

