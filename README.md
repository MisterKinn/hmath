gui/ # PySide6 GUI (main_window.py, app.py)
scripts/ # 배포/빌드 스크립트

# Formulite

## 소개

Formulite는 한글(HWP) 문서 자동화, 수식 인식, 이미지 기반 텍스트 추출, AI 기반 수식 변환 및 입력을 지원하는 통합 도구입니다. 사용자는 이미지를 업로드하거나 텍스트를 입력하여 한글 문서에 수식 및 텍스트를 자동으로 삽입할 수 있습니다.

## 주요 기능

-   이미지에서 수식 및 텍스트 자동 추출 (AI 및 OCR)
-   다양한 AI 모델(GPT, Gemini 등) 연동
-   한글(HWP) 문서 자동화 및 수식 입력
-   수식 변환(LaTeX, HWP 수식 등)
-   빠른 수식 입력 및 편집 지원

## 설치 및 실행 방법

1. Python 3.10 이상 설치
2. 필수 패키지 설치:
    ```bash
    pip install -r requirements.txt
    ```
3. (macOS) Tesseract 설치:
    ```bash
    brew install tesseract
    ```
4. .env 파일에 API 키 입력 (OpenAI, Google 등)
5. 실행:
    ```bash
    python main.py
    ```

## 사용법

-   이미지를 드래그하거나 파일로 업로드하면 자동으로 수식/텍스트가 추출되어 한글 문서에 삽입됩니다.
-   텍스트 입력 시 AI가 자동으로 수식 변환 및 입력을 지원합니다.
-   상단 메뉴에서 AI 모델을 선택할 수 있습니다(이미지 입력 시 자동으로 Gemini 사용).

## 문의 및 기여

-   버그 제보, 기능 요청, 기여는 GitHub 이슈 또는 PR로 남겨주세요.

---

본 프로젝트는 교육 및 연구 목적으로 제공되며, 상업적 사용 시 라이선스를 확인하세요.
cd node_eqn
npm install
cd ..

# 환경 변수 설정

cp .env.example .env

# .env 파일을 열고 아래 항목들을 수정하세요:

# - TESSERACT_CMD: tesseract.exe 경로

# - POPPLER_PATH: poppler bin 폴더 경로

# - 기타 필요한 설정값

````

> ⚠️ 한글과 pyhwpx는 Windows/한글 환경에서만 동작합니다. 다른 OS에서는 GUI는 뜨지만 한글 자동화가 실패합니다.

## 환경 변수 설정

이 프로젝트는 `.env` 파일을 사용하여 민감한 정보(API 키, 경로 등)를 관리합니다.

### 첫 실행 시 설정

1. `.env.example`을 복사하여 `.env` 파일을 생성합니다:
   ```bash
   cp .env.example .env
````

2. `.env` 파일을 열고 다음 항목들을 수정합니다:

    - `OPENAI_API_KEY`: [OpenAI 플랫폼](https://platform.openai.com/account/api-keys)에서 발급받은 API 키
    - `TESSERACT_CMD`: tesseract.exe의 전체 경로
    - `POPPLER_PATH`: poppler bin 폴더의 전체 경로

3. `.env` 파일은 **절대 git에 커밋하지 마세요**. `.gitignore`에 이미 등록되어 있습니다.

## 실행 방법

```powershell
python -m gui.app
```

1. **Hancom 한글**을 먼저 실행하고, 작업할 문서를 열어 커서를 원하는 위치에 둡니다.
2. 앱을 실행하면 "AMEX AI Script Console" 창이 열립니다.
3. `hwp` 객체(pyhwpx.Hwp)나 제공된 헬퍼(`insert_text`, `insert_paragraph`, `insert_image`, `insert_equation`)를 이용해 파이썬 코드를 작성하고 **실행** 버튼을 누르면 현재 문서에 즉시 반영됩니다.

예시 스크립트:

```python
insert_text("AMEX AI가 자동으로 한글 문단을 입력합니다.\\r")
insert_text("Einstein 질량-에너지 등가식은 아래와 같습니다.\\r")
insert_hwpeqn("E = m c ^{2}", font_size_pt=12.0, eq_font_name="HYhwpEQ")
```

-   `controller` 변수는 `HwpController` 인스턴스입니다.
-   `insert_*` 헬퍼들은 `hwp` 객체의 대표 기능을 감싼 래퍼라서 짧은 코드로도 결과를 확인할 수 있습니다.

## 수식 입력 (HwpEqn)

`insert_equation()`/`insert_hwpeqn()` 헬퍼는 사용자가 공유한 COM 스니펫과 동일하게
`EquationCreate → EquationPropertyDialog` 순서를 따릅니다. 즉, 수식이 생성되자마자
HancomEQN 폰트, Equation Version 60, Treat-as-char 옵션이 자동 적용되며 커서가
수식 뒤로 빠져나옵니다.

```python
# LaTeX 입력 → Node CLI로 HwpEqn 변환 후 삽입
insert_equation(r"K = \frac{1}{2} m v^{2}", font_size_pt=22.0)

# 이미 HwpEqn이라면 변환 없이 즉시 적용
insert_hwpeqn("K = {1} over {2} m v ^{2}", treat_as_char=False)
```

추가 인자:

-   `font_size_pt`: 수식의 기본 크기 (pt 단위, 기본 18pt)
-   `eq_font_name`: 수식 전용 폰트 (기본 `HancomEQN`, 예: `"HYhwpEQ"`)
-   `treat_as_char`: 글자처럼 취급 (inline) 여부
-   `ensure_newline`: 수식 뒤에 자동으로 줄바꿈을 넣고 싶을 때 `True`

## PyInstaller 빌드

PyInstaller는 `requirements.txt` 에 포함되어 있습니다. 아래 배치 스크립트는 `dist/inline-hwp-ai/inline-hwp-ai.exe` 를 만들어 줍니다.

```powershell
scripts\build_exe.bat
```

빌드 스크립트는 `node_eqn` 폴더를 그대로 묶어 두므로, 배포 시엔 `dist/inline-hwp-ai/` 전체를 전달하면 됩니다.

## TODO / 향후 작업

-   [ ] Pix2Text / pix2tex 고급 모델 연동 (현재는 pytesseract + 간단한 수식 판별)
-   [ ] 한글 수식 컨트롤에 대한 더욱 세밀한 서식 옵션
-   [ ] Poppler / Tesseract 설치 자동 감지 및 안내
-   [ ] GUI 취소 버튼 및 파일별 상세 진행률
-   [ ] 테스트 & 로깅 보강

## 참고

-   `node_eqn/` 디렉터리는 별도로 `npm install` 해야 하며, PyInstaller 빌드 시 `--add-data` 로 포함시켰습니다.
-   Hancom 한글 보안 모듈(Registry) 등록이 안 되어 있으면 pyhwpx 연결 단계에서 오류가 발생할 수 있습니다.
-   `POPPLER_PATH`, `TESSERACT_CMD`, `INLINE_HWP_*` 환경변수로 OCR 품질/성능을 조정할 수 있습니다. 자세한 옵션은 `backend/config.py` 참고.
