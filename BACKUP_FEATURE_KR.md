# 백업 기능 통합 가이드

이 문서는 FormuLite 프로젝트의 백업 기능 코드를 다른 개발자와 공유하거나 통합하는 방법을 설명합니다.

## 개요

백업 기능은 사용자가 스크립트와 세션(스크립트 + 출력)을 저장하고 복원할 수 있는 완전한 시스템입니다.

### 주요 기능

-   ✅ **커스텀 백업 이름** 지정 (비워두면 타임스탬프 자동 생성)
-   💾 **스크립트 백업** (파일 크기 및 위치 정보 포함)
-   📦 **세션 백업** (스크립트 + 출력 함께 저장)
-   🔄 **복원 대화상자** (커스텀 이름과 시간 표시)
-   ℹ️ **백업 정보 창** (통계 및 대화형 경로 메뉴)
-   🎨 **테마 인식 스타일링** (다크/라이트 모드 지원)
-   📂 **대화형 메뉴** (Finder/탐색기에서 열기, 경로 복사)

---

## 1단계: 백엔드 파일 생성

`backend/backup_manager.py` 파일을 생성하고 다음 코드를 추가하세요:

```python
"""Backup manager for FormuLite application.

Handles automatic and manual backups of scripts and settings.
"""

from __future__ import annotations

import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional


class BackupManager:
    """Manages backups of scripts and application data."""

    def __init__(self, backup_dir: Optional[Path] = None):
        """Initialize backup manager.

        Args:
            backup_dir: Directory to store backups. Defaults to ~/.formulite/backups
        """
        if backup_dir is None:
            backup_dir = Path.home() / ".formulite" / "backups"

        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)

        # Create subdirectories
        self.scripts_dir = self.backup_dir / "scripts"
        self.settings_dir = self.backup_dir / "settings"
        self.sessions_dir = self.backup_dir / "sessions"

        for directory in [self.scripts_dir, self.settings_dir, self.sessions_dir]:
            directory.mkdir(parents=True, exist_ok=True)

    def backup_script(self, script_content: str, script_name: str = "script", custom_name: str = "") -> Path:
        """Create a backup of a script.

        Args:
            script_content: The script content to backup
            script_name: Name of the script (without extension)
            custom_name: Optional custom name for the backup

        Returns:
            Path to the created backup file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if custom_name:
            backup_file = self.scripts_dir / f"{custom_name}_{timestamp}.py"
        else:
            backup_file = self.scripts_dir / f"{script_name}_{timestamp}.py"

        backup_file.write_text(script_content, encoding='utf-8')
        return backup_file

    def backup_session(self, session_data: dict, custom_name: str = "") -> Path:
        """Create a backup of a session (script + output).

        Args:
            session_data: Dictionary containing session information
                - script: The script content
                - output: The output/log content
                - timestamp: Optional timestamp
            custom_name: Optional custom name for the backup

        Returns:
            Path to the created backup file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if custom_name:
            backup_file = self.sessions_dir / f"{custom_name}_{timestamp}.json"
        else:
            backup_file = self.sessions_dir / f"session_{timestamp}.json"

        # Add backup timestamp if not present
        if "backup_timestamp" not in session_data:
            session_data["backup_timestamp"] = timestamp

        backup_file.write_text(json.dumps(session_data, indent=2, ensure_ascii=False), encoding='utf-8')
        return backup_file

    def get_recent_backups(self, backup_type: str = "scripts", limit: int = 10) -> list[Path]:
        """Get recent backup files.

        Args:
            backup_type: Type of backup ('scripts', 'sessions', or 'settings')
            limit: Maximum number of backups to return

        Returns:
            List of backup file paths, sorted by modification time (newest first)
        """
        if backup_type == "scripts":
            directory = self.scripts_dir
        elif backup_type == "sessions":
            directory = self.sessions_dir
        elif backup_type == "settings":
            directory = self.settings_dir
        else:
            raise ValueError(f"Unknown backup type: {backup_type}")

        backups = sorted(directory.glob("*"), key=lambda p: p.stat().st_mtime, reverse=True)
        return backups[:limit]

    def restore_backup(self, backup_file: Path) -> str | dict:
        """Restore content from a backup file.

        Args:
            backup_file: Path to the backup file

        Returns:
            Content of the backup (str for scripts, dict for sessions)

        Raises:
            FileNotFoundError: If backup file doesn't exist
        """
        if not backup_file.exists():
            raise FileNotFoundError(f"Backup file not found: {backup_file}")

        if backup_file.suffix == ".json":
            return json.loads(backup_file.read_text(encoding='utf-8'))
        else:
            return backup_file.read_text(encoding='utf-8')

    def delete_backup(self, backup_file: Path) -> bool:
        """Delete a backup file.

        Args:
            backup_file: Path to the backup file

        Returns:
            True if deletion was successful, False otherwise
        """
        try:
            backup_file.unlink()
            return True
        except Exception as e:
            print(f"Error deleting backup: {e}")
            return False

    def cleanup_old_backups(self, backup_type: str = "scripts", keep_count: int = 20) -> int:
        """Remove old backups, keeping only the most recent ones.

        Args:
            backup_type: Type of backup to clean up
            keep_count: Number of recent backups to keep

        Returns:
            Number of backups deleted
        """
        backups = self.get_recent_backups(backup_type, limit=1000)

        if len(backups) <= keep_count:
            return 0

        deleted_count = 0
        for backup_file in backups[keep_count:]:
            if self.delete_backup(backup_file):
                deleted_count += 1

        return deleted_count

    def export_backups(self, export_path: Path) -> bool:
        """Export all backups to a zip file.

        Args:
            export_path: Path where to save the exported zip file

        Returns:
            True if export was successful, False otherwise
        """
        try:
            shutil.make_archive(
                str(export_path.with_suffix('')),
                'zip',
                self.backup_dir
            )
            return True
        except Exception as e:
            print(f"Error exporting backups: {e}")
            return False

    def get_backup_info(self, backup_file: Path) -> dict:
        """Get information about a backup file.

        Args:
            backup_file: Path to the backup file

        Returns:
            Dictionary with backup information
        """
        stat = backup_file.stat()
        # Extract custom name from filename (format: name_YYYYMMDD_HHMMSS.ext)
        filename = backup_file.stem
        parts = filename.rsplit('_', 2)
        if len(parts) >= 3 and parts[-2].isdigit() and parts[-1].isdigit():
            custom_name = parts[0]
            timestamp_str = f"{parts[-2]}_{parts[-1]}"
            try:
                timestamp_dt = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
                formatted_time = timestamp_dt.strftime("%Y-%m-%d %H:%M:%S")
            except:
                formatted_time = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
        else:
            custom_name = filename
            formatted_time = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")

        return {
            "name": backup_file.name,
            "custom_name": custom_name,
            "formatted_time": formatted_time,
            "path": str(backup_file),
            "size": stat.st_size,
            "created": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            "type": backup_file.suffix
        }

    def get_all_backup_stats(self) -> dict:
        """Get statistics about all backups.

        Returns:
            Dictionary with backup statistics
        """
        stats = {
            "scripts": {
                "count": len(list(self.scripts_dir.glob("*"))),
                "total_size": sum(f.stat().st_size for f in self.scripts_dir.glob("*"))
            },
            "sessions": {
                "count": len(list(self.sessions_dir.glob("*"))),
                "total_size": sum(f.stat().st_size for f in self.sessions_dir.glob("*"))
            },
            "settings": {
                "count": len(list(self.settings_dir.glob("*"))),
                "total_size": sum(f.stat().st_size for f in self.settings_dir.glob("*"))
            },
            "backup_dir": str(self.backup_dir)
        }
        return stats
```

---

## 2단계: GUI 파일 수정 (`gui/main_window.py`)

### 2.1 임포트 추가

main_window.py 파일 상단에 밑의 코드를 복붙하세요:

```python
from backend.backup_manager import BackupManager
from PySide6.QtGui import QDesktopServices
from PySide6.QtCore import QUrl
from PySide6.QtWidgets import QLineEdit, QDialogButtonBox
```

### 2.2 초기화 메서드 수정

`MainWindow` 클래스의 `__init__` 메서드에 다음을 추가하세요:

```python
def __init__(self):
    super().__init__()
    # ... 기존 코드 ...

    # BackupManager 초기화
    self.backup_manager = BackupManager()

    # ... 나머지 코드 ...
```

### 2.3 백업 아이콘 버튼 추가

사이드바에 백업 버튼을 추가하세요 (보통 `_build_ui` 메서드에서):

```python
# 백업 버튼
self.backup_icon_btn = QToolButton()
self.backup_icon_btn.setObjectName("pin-button")
self.backup_icon_btn.setToolTip("백업 및 복원")
self.backup_icon_btn.setAutoRaise(True)
self.backup_icon_btn.setText("[B]")
self._apply_button_icon_themed(self.backup_icon_btn, "backup_icon", "[B]", QSize(32, 32))
self.backup_icon_btn.clicked.connect(self._show_backup_menu)
```

### 2.4 백업 메서드 추가

다음 메서드들을 `MainWindow` 클래스에 추가하세요:

1. **`_show_backup_menu()`** - 백업 메뉴 표시
2. **`_backup_current_script()`** - 현재 스크립트 백업
3. **`_backup_session()`** - 세션 백업 (스크립트 + 출력)
4. **`_restore_script_dialog()`** - 스크립트 복원 대화상자
5. **`_restore_session_dialog()`** - 세션 복원 대화상자
6. **`_show_backup_info()`** - 백업 정보 창 표시

전체 메서드 코드는 프로젝트의 `gui/main_window.py` 파일 2137-2720 라인을 참조하세요.

---

## 3단계: 아이콘 파일 추가

`public/img/` 디렉토리에 백업 아이콘을 추가하세요:

-   `backup_icon.png` (다크 모드용)
-   `backup_icon_black.png` (라이트 모드용)

---

## 사용 방법

### 백업 생성

1. 사이드바의 백업 아이콘 클릭
2. "현재 스크립트 백업" 또는 "세션 백업" 선택
3. 백업 이름 입력 (선택사항, 비워두면 타임스탬프 자동 생성)
4. 완료 대화상자에서 백업 정보 확인
    - 파일명, 크기, 위치 표시
    - "⋯" 메뉴로 Finder/탐색기에서 열기 또는 경로 복사 가능

### 백업 복원

1. 백업 아이콘 → "스크립트 복원" 또는 "세션 복원" 선택
2. 복원할 백업 선택 (커스텀 이름과 시간 표시됨)
3. "복원" 버튼 클릭

### 백업 정보 보기

1. 백업 아이콘 → "백업 정보 보기" 선택
2. 스크립트/세션 통계 확인
3. 백업 위치 경로 확인 및 접근

---

## 파일 구조

백업은 기본적으로 다음 위치에 저장됩니다:

```
~/.formulite/backups/
├── scripts/          # 스크립트 백업 (.py 파일)
├── sessions/         # 세션 백업 (.json 파일)
└── settings/         # 설정 백업 (향후 사용)
```

파일 이름 형식:

-   스크립트: `{custom_name}_{YYYYMMDD_HHMMSS}.py`
-   세션: `{custom_name}_{YYYYMMDD_HHMMSS}.json`

---
