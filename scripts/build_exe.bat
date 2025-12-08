@echo off
setlocal enabledelayedexpansion

REM PyInstaller 빌드 스크립트
REM 사용법: scripts\build_exe.bat

pushd "%~dp0\.."

if not exist node_eqn\node_modules (
    echo [INFO] node_eqn\node_modules 가 없습니다. npm install 을 먼저 실행하세요.
    popd
    exit /b 1
)

set PYTHON_EXE=python
where %PYTHON_EXE% >nul 2>&1
if errorlevel 1 (
    echo [ERROR] python 실행 파일을 찾을 수 없습니다.
    popd
    exit /b 1
)

%PYTHON_EXE% -m PyInstaller ^
    --noconfirm ^
    --clean ^
    --name inline-hwp-ai ^
    --add-data "node_eqn;node_eqn" ^
    gui\app.py

if errorlevel 1 (
    echo [ERROR] PyInstaller 빌드가 실패했습니다.
    popd
    exit /b 1
)

echo [OK] dist\inline-hwp-ai\inline-hwp-ai.exe 생성 완료
popd
endlocal

