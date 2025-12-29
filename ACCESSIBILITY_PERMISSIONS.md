# ⚠️ IMPORTANT: Accessibility Permissions Required!

## macOS에서 앱을 사용하려면 접근성 권한이 필요합니다

### 왜 필요한가요?
macOS Formulite는 AppleScript를 사용하여 Hancom Office HWP에 텍스트를 입력합니다.
이를 위해서는 **시스템 접근성 권한**이 필요합니다.

### 오류 메시지
권한이 없으면 이런 오류가 발생합니다:
```
System Events got an error: osascript is not allowed to send keystrokes. (1002)
```

---

## 🔧 해결 방법 (Step-by-Step)

### 1단계: 시스템 설정 열기
- **Spotlight 검색** (⌘ + Space) → "시스템 설정" 또는 "System Settings"
- 또는: Apple 메뉴 () → 시스템 설정

### 2단계: 개인 정보 보호 및 보안
- 왼쪽 사이드바에서 **"개인 정보 보호 및 보안"** (Privacy & Security) 클릭

### 3단계: 손쉬운 사용 (Accessibility)
- 오른쪽 목록에서 **"손쉬운 사용"** (Accessibility) 클릭
- 🔒 자물쇠 아이콘을 클릭하고 비밀번호 입력 (잠금 해제)

### 4단계: Terminal 추가
- **"+"** 버튼 클릭
- **Applications** → **Utilities** → **Terminal** 선택
  - (또는 iTerm, Warp 등 사용 중인 터미널 앱)
- **열기(Open)** 클릭

### 5단계: 토글 활성화
- 목록에서 **Terminal** 찾기
- ✅ **토글을 켜기** (체크박스 활성화)

### 6단계: 터미널 재시작
```bash
# 현재 터미널을 종료하고 다시 열기
exit
```
또는 터미널 앱을 완전히 종료했다가 다시 실행하세요.

---

## ✅ 확인하기

권한 설정 후 다시 실행:
```bash
cd /Users/kinn/Desktop/formulite
python3 check_macos.py
```

또는 테스트:
```bash
osascript -e 'tell application "System Events" to keystroke "test"'
```

오류 없이 실행되면 **성공!** 🎉

---

## 🖼️ 스크린샷 가이드

### 시스템 설정 위치:
```
 Apple 메뉴
  └─ 시스템 설정 (System Settings)
      └─ 개인 정보 보호 및 보안 (Privacy & Security)
          └─ 손쉬운 사용 (Accessibility)
              └─ [+] Terminal 추가
```

### 확인 사항:
- [x] Terminal이 목록에 있음
- [x] 토글이 켜져 있음 (파란색/녹색)
- [x] 터미널을 재시작함

---

## 🚨 자주 묻는 질문

### Q: "Terminal이 이미 목록에 있는데 안 돼요"
**A:** 토글을 **끄고 다시 켜기**:
1. 토글 클릭 → 비활성화
2. 3초 대기
3. 토글 다시 클릭 → 활성화
4. 터미널 재시작

### Q: "Terminal 대신 다른 앱을 써요 (iTerm, Warp 등)"
**A:** 사용 중인 터미널 앱을 추가하세요:
- iTerm 사용자 → iTerm.app 추가
- Warp 사용자 → Warp.app 추가
- 여러 개 추가해도 괜찮습니다!

### Q: "Python.app도 추가해야 하나요?"
**A:** 대부분의 경우 Terminal만으로 충분합니다. 
하지만 안 되면 Python.app도 추가해보세요.

### Q: "VS Code / Cursor에서 실행하는데 안 돼요"
**A:** VS Code 또는 Cursor를 Accessibility 목록에 추가하세요:
- Applications → Visual Studio Code.app
- 또는 Cursor.app

### Q: "권한을 줬는데도 계속 오류가 나요"
**A:** 다음을 시도하세요:
1. 터미널 **완전 종료** 후 재시작
2. 맥 **재시작**
3. Accessibility 목록에서 Terminal **제거 후 다시 추가**

---

## 🔒 보안 걱정?

### "이 권한은 안전한가요?"
네! Accessibility 권한은:
- ✅ 키보드 입력을 시뮬레이션하기 위해 필요
- ✅ Formulite는 HWP 앱에만 텍스트 전송
- ✅ 오픈소스 - 코드를 직접 확인 가능
- ✅ 언제든지 시스템 설정에서 권한 제거 가능

### "나중에 권한을 제거하려면?"
1. 시스템 설정 → 개인 정보 보호 및 보안 → 손쉬운 사용
2. Terminal 선택
3. **"-"** 버튼 클릭
4. 완료!

---

## ✨ 설정 완료 후

권한을 설정했다면 이제 앱을 사용할 수 있습니다:

```bash
# 1. Hancom Office HWP 실행 (문서 열기)
# 2. 앱 실행
./start_macos.sh

# 3. 명령 입력
"안녕하세요를 입력해줘"

# 4. Enter 누르기
# 5. HWP 문서 확인! 🎉
```

---

**도움이 필요하면 MACOS_SETUP.md를 참고하세요!**


