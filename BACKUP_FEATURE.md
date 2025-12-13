# Backup Feature Documentation

## Overview

The FormuLite application now includes a comprehensive backup system that allows you to save and restore your scripts and sessions automatically or manually.

## Features

### 1. **Script Backup**
   - Creates a timestamped backup of your current script
   - Saves to: `~/.formulite/backups/scripts/`
   - Format: `script_YYYYMMDD_HHMMSS.py`

### 2. **Session Backup**
   - Saves both script and output/log content together
   - Useful for preserving complete work sessions
   - Saves to: `~/.formulite/backups/sessions/`
   - Format: `session_YYYYMMDD_HHMMSS.json`

### 3. **Restore Functionality**
   - Browse and restore previously backed-up scripts
   - Browse and restore complete sessions
   - Shows backup creation timestamp for easy identification

### 4. **Backup Information**
   - View statistics about all backups
   - See total number of backups
   - View backup storage location
   - Check total storage size used

## How to Use

### Accessing Backup Features

1. Click the **"백업"** (Backup) button in the top toolbar
2. A dropdown menu will appear with the following options:
   - 현재 스크립트 백업 (Backup Current Script)
   - 세션 백업 (Backup Session)
   - 스크립트 복원 (Restore Script)
   - 세션 복원 (Restore Session)
   - 백업 정보 보기 (View Backup Info)

### Creating a Backup

#### Manual Script Backup:
1. Click "백업" → "현재 스크립트 백업"
2. Confirmation dialog shows backup location and size
3. Script is saved with timestamp

#### Manual Session Backup:
1. Click "백업" → "세션 백업 (스크립트 + 출력)"
2. Both current script and output are saved together
3. Confirmation dialog shows backup details

### Restoring from Backup

#### Restore a Script:
1. Click "백업" → "스크립트 복원..."
2. Select from list of available backups (up to 20 most recent)
3. Click "복원" button
4. Selected script replaces current editor content

#### Restore a Session:
1. Click "백업" → "세션 복원..."
2. Select from list of available sessions
3. Click "복원" button
4. Both script and output are restored

### Viewing Backup Information

1. Click "백업" → "백업 정보 보기"
2. Dialog shows:
   - Number of script backups
   - Total size of script backups
   - Number of session backups
   - Total size of session backups
   - Backup directory location

## Backup Storage

### Default Location
- **macOS/Linux**: `~/.formulite/backups/`
- **Windows**: `C:\Users\<YourUsername>\.formulite\backups\`

### Directory Structure
```
~/.formulite/
├── backups/
│   ├── scripts/        # Script backups (*.py)
│   ├── sessions/       # Session backups (*.json)
│   └── settings/       # Settings backups (reserved for future use)
```

## Technical Details

### BackupManager Class

Located in: `backend/backup_manager.py`

#### Key Methods:

- `backup_script(script_content, script_name)` - Create script backup
- `backup_session(session_data)` - Create session backup
- `get_recent_backups(backup_type, limit)` - Retrieve recent backups
- `restore_backup(backup_file)` - Restore from backup file
- `delete_backup(backup_file)` - Delete specific backup
- `cleanup_old_backups(backup_type, keep_count)` - Auto-cleanup old backups
- `get_backup_info(backup_file)` - Get backup file information
- `get_all_backup_stats()` - Get statistics

### Session Data Format

Session backups are stored as JSON with the following structure:

```json
{
  "script": "// Python script content here",
  "output": "// Log output here",
  "backup_timestamp": "20231215_143025"
}
```

## Best Practices

1. **Regular Backups**: Create backups before major script changes
2. **Session Preservation**: Use session backups to preserve complete work contexts
3. **Storage Management**: The system keeps recent backups; older ones can be deleted manually
4. **Naming Convention**: Backups are auto-timestamped for easy identification

## Limitations

- Up to 20 recent backups are shown in restore dialogs
- Backup manager keeps up to 20 script and session backups by default
- Old backups can be manually deleted from `~/.formulite/backups/`

## Future Enhancements

Potential features for future releases:

- Automatic backup intervals
- Backup compression
- Cloud backup support
- Backup versioning with diff view
- Backup export/import functionality
- Settings backup and restore

## Troubleshooting

### Backups Not Showing in Restore Dialog
- Check that `~/.formulite/backups/` directory exists
- Ensure you have write permissions in the home directory
- Create a new backup to verify the system is working

### Cannot Find Backup Location
- Use the "백업 정보 보기" option to see exact backup directory path
- Navigate there manually to browse backup files

### Error Creating Backup
- Ensure sufficient disk space available
- Check write permissions on home directory
- Try creating another backup to verify the issue

## Support

For issues or feature requests related to the backup system, please refer to the main application documentation or contact the development team.
