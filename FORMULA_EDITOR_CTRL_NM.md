# 📐 수식 입력 창 (Formula Input Window) - Ctrl+N+M

## ✅ 구현 완료!

한글 앱의 **수식 입력 창**을 Ctrl+N+M 단축키로 자동으로 열 수 있습니다!

## 🚀 사용 방법

### 방법 1: 수식 편집기만 열기

```python
from backend.hwp.hwp_controller import HwpController

hwp = HwpController()
hwp.connect()

# 수식 입력 창 열기 (Ctrl+N+M)
hwp.open_formula_editor()

# 이제 수동으로 수식을 입력할 수 있습니다
```

### 방법 2: 자동으로 수식 삽입

```python
from backend.hwp.hwp_controller import HwpController

hwp = HwpController()
hwp.connect()

# 수식 입력 창을 열고 자동으로 수식 삽입
hwp.insert_equation_via_editor("a over b")
# 결과: 실제 분수 수식 객체가 삽입됨
```

## 📝 수식 편집기 문법

한글 수식 편집기는 간단한 영어 문법을 사용합니다:

### 분수
```
a over b          → a/b (분수)
x^2 + y^2 over z^2  → (x² + y²)/z²
```

### 제곱
```
x^2               → x²
x^(n+1)           → xⁿ⁺¹
```

### 아래첨자
```
x_1               → x₁
H_2O              → H₂O
```

### 적분
```
int from 0 to infinity
int from a to b
int
```

### 합
```
sum from i=1 to n
sum from 1 to 10
sum
```

### 그리스 문자
```
alpha, beta, gamma, pi, theta, etc.
```

## 🎯 예제

### 예제 1: 간단한 분수
```python
hwp.insert_equation_via_editor("a over b")
```

### 예제 2: 제곱
```python
hwp.insert_equation_via_editor("x^2 + y^2")
```

### 예제 3: 적분
```python
hwp.insert_equation_via_editor("int from 0 to infinity e^-x dx")
```

### 예제 4: 복잡한 수식
```python
hwp.insert_equation_via_editor("(x^2 + y^2) over z^2")
```

## 🔧 테스트

테스트 스크립트 실행:

```bash
python3 test_formula_editor_ctrl_nm.py
```

이 스크립트는:
1. 수식 입력 창 열기 테스트
2. 자동 수식 삽입 테스트
3. 복잡한 수식 테스트

## 💡 AI 사용

AI에게 요청하면 자동으로 `insert_equation_via_editor()`를 사용합니다:

```
User: "분수 a/b를 실제 수식으로 삽입해줘"
AI: *generates code with insert_equation_via_editor("a over b")*
Result: ✅ 실제 수식 객체가 삽입됨
```

## ⚖️ 비교

### insert_math_text() vs insert_equation_via_editor()

| 특징 | insert_math_text() | insert_equation_via_editor() |
|------|-------------------|------------------------------|
| 타입 | Unicode 텍스트 | 실제 수식 객체 |
| 품질 | 좋음 | 매우 좋음 |
| 편집 | 일반 텍스트처럼 | 수식 편집기로 편집 가능 |
| 속도 | 빠름 | 약간 느림 (창 열기) |
| 사용 | 간단한 수식 | 복잡한 수식, 실제 수식 필요 시 |

### 언제 무엇을 사용할까?

**insert_math_text() 사용:**
- 빠른 수식 삽입
- 간단한 수식 (x², α, ∫ 등)
- 텍스트로 충분한 경우

**insert_equation_via_editor() 사용:**
- 실제 수식 객체 필요
- 복잡한 수식 (분수, 적분, 행렬 등)
- 나중에 편집해야 하는 수식
- 전문적인 문서 작성

## 🔍 작동 원리

1. **Ctrl+N+M 입력:**
   ```applescript
   keystroke "n" using control down  -- Control+N
   delay 0.1
   keystroke "m" using control down  -- Control+M
   ```

2. **수식 입력 창 열림:**
   - 한글 앱에서 수식 입력 창이 열림
   - 입력 필드에 포커스

3. **수식 입력:**
   - 클립보드에 수식 복사
   - ⌘V로 붙여넣기
   - Enter로 확인 및 삽입

## ⚠️ 주의사항

1. **Accessibility 권한 필요:**
   - System Settings → Privacy & Security → Accessibility
   - Terminal 추가 및 활성화

2. **한글 앱 실행 필요:**
   - Hancom Office HWP가 실행 중이어야 함
   - 문서가 열려 있어야 함

3. **수식 문법:**
   - 한글 수식 편집기 문법 사용
   - LaTeX 문법이 아님
   - 예: `\frac{a}{b}` ❌ → `a over b` ✅

## 📚 관련 파일

- `backend/hwp/hwp_macos.py` - `open_formula_editor()`, `insert_equation_via_editor()`
- `backend/hwp/hwp_controller.py` - Controller wrapper
- `test_formula_editor_ctrl_nm.py` - 테스트 스크립트

## 🎉 완료!

이제 Ctrl+N+M 단축키로 수식 입력 창을 자동으로 열고 수식을 삽입할 수 있습니다!

---

**Status:** ✅ Complete
**Shortcut:** Ctrl+N+M
**Method:** AppleScript automation


