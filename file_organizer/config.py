#!/usr/bin/env python3
"""
Configuration file for File Organizer script.
Defines file type mappings, folder structures, and settings.
"""

from pathlib import Path
from typing import Dict, List, Set

# Default directory to organize (if not specified via CLI)
# DEFAULT_TARGET_DIR = Path.home() / "Downloads"
DEFAULT_TARGET_DIR = "tmp"

# File extension to folder name mappings
FILE_CATEGORIES: Dict[str, str] = {
    # Images
    '.jpg': 'Images',
    '.jpeg': 'Images',
    '.png': 'Images',
    '.gif': 'Images',
    '.bmp': 'Images',
    '.svg': 'Images',
    '.ico': 'Images',
    '.webp': 'Images',

    # Documents
    '.pdf': 'Documents',
    '.doc': 'Documents',
    '.docx': 'Documents',
    '.txt': 'Documents',
    '.rtf': 'Documents',
    '.odt': 'Documents',
    '.md': 'Documents',

    # Spreadsheets
    '.xls': 'Spreadsheets',
    '.xlsx': 'Spreadsheets',
    '.csv': 'Spreadsheets',
    '.ods': 'Spreadsheets',

    # Presentations
    '.ppt': 'Presentations',
    '.pptx': 'Presentations',
    '.odp': 'Presentations',

    # Archives
    '.zip': 'Archives',
    '.tar': 'Archives',
    '.gz': 'Archives',
    '.bz2': 'Archives',
    '.7z': 'Archives',
    '.rar': 'Archives',

    # Code
    '.py': 'Code',
    '.js': 'Code',
    '.go': 'Code',
    '.html': 'Code',
    '.css': 'Code',
    '.json': 'Code',
    '.xml': 'Code',
    '.yaml': 'Code',
    '.yml': 'Code',
    '.sh': 'Code',
    '.bat': 'Code',
    '.ps1': 'Code',

    # Videos
    '.mp4': 'Videos',
    '.mkv': 'Videos',
    '.avi': 'Videos',
    '.mov': 'Videos',
    '.wmv': 'Videos',
    '.flv': 'Videos',
    '.webm': 'Videos',

    # Audio
    '.mp3': 'Audio',
    '.wav': 'Audio',
    '.flac': 'Audio',
    '.aac': 'Audio',
    '.ogg': 'Audio',
    '.m4a': 'Audio',

    # Executables
    '.exe': 'Executables',
    '.msi': 'Executables',
    '.app': 'Executables',
    '.deb': 'Executables',
    '.rpm': 'Executables',
    '.dmg': 'Executables',
}

# Extensions to skip (don't move)
IGNORED_EXTENSIONS: Set[str] = {
    '.tmp',
    '.temp',
    '.log',
    '.lock',
    '.part',
    '.crdownload',  # Chrome partial download
    '.download',     # Generic partial download
}

# Extensions that should be treated as "Other" (not in categories above)
OTHER_CATEGORY = "Other"

# Folders to always create (even if no files of that type)
ALWAYS_CREATE_FOLDERS: List[str] = [
    'Images',
    'Documents',
    'Archives',
    'Code',
    'Other'
]

# Conflict resolution strategies
# 'rename' - add number suffix (file_1.txt)
# 'overwrite' - replace existing file
# 'skip' - leave file in original location
CONFLICT_RESOLUTION = 'rename'  # Options: 'rename', 'overwrite', 'skip'

# Dry run mode (no actual file operations)
DRY_RUN_BY_DEFAULT = True

# Enable verbose logging by default
VERBOSE_BY_DEFAULT = False

# Log file location
# LOG_FILE = Path.home() / ".file_organizer.log"
# LOG_FILE = "file_organizer/logs/file_organizer.log"
# Get the directory where this script is located
SCRIPT_DIR = Path(__file__).parent.absolute()
LOG_FILE = SCRIPT_DIR / "logs" / "file_organizer.log"

# Stats to display after organization
SHOW_STATS = True

# Use Rich for pretty console output (if available)
USE_RICH = True
