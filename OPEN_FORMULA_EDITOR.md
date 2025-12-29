# 📐 수식 편집기 창 자동 열기

## ✅ 네, 가능합니다!

프로그램이 **수식 편집기 (Formula Editor)** 창을 자동으로 열 수 있습니다!

AI가 **"입력 → 수식..."** 메뉴를 클릭하여 수식 창을 자동으로 열 수 있습니다.

## 🚀 사용 방법

### 방법 1: 코드에서 직접 사용

```python
from backend.hwp.hwp_controller import HwpController

hwp = HwpController()
hwp.connect()

# 수식 편집기 창 열기 (입력 → 수식... 메뉴 클릭)
hwp.open_formula_editor()

# 이제 사용자가 수동으로 수식을 입력할 수 있습니다
```

### 방법 2: AI를 통해 사용

```
User: "수식 편집기를 열어줘"
AI: *generates code with open_formula_editor()*
Result: ✅ 수식 편집기 창이 열림
```

### 방법 3: 스크립트에서 사용

```python
# 코드 입력 창에서:
open_formula_editor()
```

## 🔧 작동 원리

1. **메뉴 클릭 (우선순위 순서):**
   ```applescript
   -- Method 1: 입력 → 수식... (가장 일반적)
   click menu item "수식..." of menu "입력" of menu bar 1
   
   -- Method 2: 입력 → 수식 (ellipsis 없음)
   click menu item "수식" of menu "입력" of menu bar 1
   
   -- Method 3: 삽입 → 수식 (이전 버전)
   click menu item "수식" of menu "삽입" of menu bar 1
   
   -- Method 4: 삽입 → 수식 편집기
   click menu item "수식 편집기" of menu "삽입" of menu bar 1
   
   -- Method 5: English menu
   click menu item "Equation" of menu "Input" of menu bar 1
   
   -- Method 6: 단축키 fallback
   keystroke "e" using {option down, command down}
   ```

2. **수식 편집기 창 열림:**
   - 한글 앱에서 수식 편집기 창이 자동으로 열림
   - 사용자가 수식을 입력할 수 있음

## 📝 사용 예시

### 예시 1: 수식 편집기 열기
```python
hwp.open_formula_editor()
# 결과: 수식 편집기 창이 열림
# 사용자가 수동으로 수식을 입력하고 "넣기" 버튼 클릭
```

### 예시 2: AI 요청
```
User: "수식 편집기를 열어줘"
AI: open_formula_editor()
Result: ✅ 창이 열림
```

### 예시 3: 자동 수식 삽입과 비교
```python
# 방법 1: 수동 입력 (사용자가 직접 입력)
hwp.open_formula_editor()

# 방법 2: 자동 삽입 (프로그램이 자동으로 입력)
hwp.insert_equation_via_editor("a over b")
```

## 🎯 언제 사용하나요?

**open_formula_editor() 사용:**
- 사용자가 직접 수식을 입력하고 싶을 때
- 복잡한 수식을 수동으로 만들고 싶을 때
- 수식 편집기의 도구를 사용하고 싶을 때

**insert_equation_via_editor() 사용:**
- 프로그램이 자동으로 수식을 삽입할 때
- 간단한 수식을 빠르게 삽입할 때

## 🧪 테스트

테스트 스크립트 실행:

```bash
# 새로운 테스트 (입력 메뉴 테스트)
python3 test_input_menu_formula.py

# 기존 테스트
python3 test_open_formula_editor.py
```

새로운 테스트 스크립트 (`test_input_menu_formula.py`)는:
1. 한글에 연결
2. "입력 → 수식..." 메뉴 클릭
3. 수식 편집기 창이 열렸는지 확인
4. 자동으로 "a over b" 분수 삽입 테스트

## ⚠️ 주의사항

1. **Accessibility 권한 필요:**
   - System Settings → Privacy & Security → Accessibility
   - Terminal 추가 및 활성화

2. **한글 앱 실행 필요:**
   - Hancom Office HWP가 실행 중이어야 함
   - 문서가 열려 있어야 함

3. **메뉴 경로:**
   - 주 경로: **입력 → 수식...**
   - 대체 경로: 삽입 → 수식 (이전 버전)
   - 영문 메뉴: Input → Equation
   - 단축키: Option+Command+E (fallback)

## 📚 관련 함수

- `open_formula_editor()` - 수식 편집기 창만 열기 (입력 → 수식 메뉴)
- `insert_equation_via_editor(formula)` - 수식 편집기를 열고 자동으로 수식 삽입

## 💡 팁

1. **수동 입력:**
   ```python
   hwp.open_formula_editor()
   # 사용자가 수식을 입력하고 "넣기" 클릭
   ```

2. **자동 삽입:**
   ```python
   hwp.insert_equation_via_editor("a over b")
   # 프로그램이 자동으로 수식 삽입
   ```

3. **AI 요청:**
   ```
   "수식 편집기를 열어줘" → open_formula_editor()
   "분수 a/b를 삽입해줘" → insert_equation_via_editor("a over b")
   ```

## 🆕 업데이트 내역

**2024-12-29:**
- ✅ "입력 → 수식..." 메뉴 경로 추가
- ✅ 여러 메뉴 경로를 시도하도록 개선 (입력/삽입 메뉴 모두 지원)
- ✅ 새로운 테스트 스크립트 추가: `test_input_menu_formula.py`
- ✅ 더 나은 에러 메시지 추가

---

**Status:** ✅ Complete
**Menu Path:** 입력 → 수식... (우선) / 삽입 → 수식 (대체)
**Method:** AppleScript menu automation + Keyboard shortcut fallback


