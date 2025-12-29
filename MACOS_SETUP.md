# macOS 한글 Integration Guide

## 🎉 Good News!
Your Formulite app now works on **macOS** with 한글 (Hancom Hangul)!

## 📋 Requirements

1. **macOS** (any recent version)
2. **한글 (Hancom Office Hangul)** installed
3. **Python 3.8+**

## 🚀 Setup Instructions

### 1. Install Dependencies
```bash
cd /Users/kinn/Desktop/formulite
pip install -r requirements.txt
```

### 2. Grant Accessibility Permissions
macOS requires accessibility permissions for automation:

1. Open **System Settings** > **Privacy & Security** > **Accessibility**
2. Add **Terminal** (or your terminal app) to the list
3. Enable the toggle

**Important:** Without this, the app won't be able to control 한글!

### 3. Test the Integration

```bash
# Step 1: Open 한글 and create a new document
# Step 2: Keep it open in the background

# Step 3: Run the test script
python test_hwp_macos.py
```

If you see text appear in your 한글 document, **it works!** 🎉

## 🎮 Usage

### Method 1: Quick Test
```bash
# 1. Open 한글 with a document
# 2. Run test
python test_hwp_macos.py
```

### Method 2: Full App
```bash
# 1. Open 한글 with a document
# 2. Run the app
python -m gui.app

# 3. Type: "안녕하세요를 입력해줘"
# 4. Press Enter
# 5. Check your 한글 document!
```

## 🔧 How It Works

### Windows vs macOS

| Feature | Windows | macOS |
|---------|---------|-------|
| Backend | `pyhwpx` (COM) | AppleScript automation |
| Installation | Requires `pywin32` | Built-in (no extra packages) |
| Document Access | Direct API | Simulated keystrokes |
| Equation Support | ✅ Full support | ⚠️ Text only (for now) |

### macOS Limitations

**Current limitations:**
- ⚠️ **Equations:** LaTeX equations not supported yet (Windows only)
- ⚠️ **Formatting:** Advanced formatting not available
- ✅ **Text insertion:** Works perfectly
- ✅ **Paragraphs:** Works perfectly

**Why?** 한글 on macOS doesn't expose a COM/automation API like Windows. We use AppleScript to simulate keyboard input instead.

## 🐛 Troubleshooting

### Error: "한글(HWP) 프로그램이 실행 중이지 않습니다"

**Solution:**
1. Open 한글 application
2. Create or open a document
3. **Keep it in the background** (don't close it)
4. Run the app again

### Error: "AppleScript execution timed out"

**Solution:**
1. Grant Accessibility permissions (see Setup step 2)
2. Make sure 한글 is responding (not frozen)
3. Try quitting and reopening 한글

### Error: "operation not permitted"

**Solution:**
1. Open **System Settings** > **Privacy & Security** > **Accessibility**
2. Add your terminal app to the list
3. Restart terminal
4. Try again

### Text appears in wrong app

**Solution:**
- Make sure 한글 is the **frontmost** application when you press Enter
- The app will automatically activate 한글, but timing matters
- Try clicking on 한글 window before running the command

## 🎯 Best Practices

### ✅ DO:
- Open 한글 **before** running the app
- Create a new document or open an existing one
- Keep 한글 visible or in background
- Use for simple text insertion and paragraphs

### ❌ DON'T:
- Close 한글 while the app is running
- Expect LaTeX equations to work (Windows only for now)
- Use complex formatting commands
- Run multiple instances simultaneously

## 🔮 Future Improvements

### Planned Features:
1. 🎯 **LaTeX Support on macOS** - Using image insertion workaround
2. 🎨 **Formatting** - Bold, italic, colors via AppleScript
3. 🚀 **Better Detection** - Auto-detect 한글 installation
4. 📱 **UI Feedback** - Show connection status in GUI

### Won't Fix:
- ❌ Full COM API on macOS (not possible)
- ❌ Native equation editing (no API available)

## 📞 Need Help?

### Quick Checks:
1. ✅ 한글 is installed and can open manually?
2. ✅ Python 3.8+ installed? (`python3 --version`)
3. ✅ Accessibility permissions granted?
4. ✅ 한글 is running with a document open?

### Still stuck?
1. Run the test script: `python test_hwp_macos.py`
2. Check the console output for specific errors
3. Try the Windows version if you have access to a Windows PC

## 🎊 Success!

If you see this in your 한글 document after running the test:

```
안녕하세요! macOS 한글 테스트입니다.
이 문장이 보이면 성공입니다! 🎉
```

**Congratulations! Your macOS 한글 integration is working!** 🚀

---

Made with ❤️ for macOS + 한글 users


