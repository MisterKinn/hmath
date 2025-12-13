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
