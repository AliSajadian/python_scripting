#!/venv/bin/python3
"""
Configuration of Log Analyser script.
Define log patterns, aggregation rules, analysis settings.
"""

from pathlib import Path
from typing import List, Dict, Pattern
import re

# Project root directory
PROJECT_ROOT = Path(__file__).parent.absolute()

# Default log file
DEFAULT_LOG_FILE = PROJECT_ROOT / "logs" / "analyzer.log"

# Log level mappimg
LOG_LEVEL = {
    'DEBUG'   : 10,
    'INFO'    : 20,
    'WARNING' : 30,
    'ERROR'   : 40,
    'CRITICAL' : 50
}

# Regex patterns for common log format
PATTENS = Dict[str, Pattern] = {
    # Standard syslog format: 16 May 01:10:30 server app[1234]: message
    'syslog': re.compile(
        ''
    ),

    # Common log format: 2026-05-16 01:10:30, 123 ERROR module: message
    'commomn': re.compile(
        ''
    ),

    # Simple format: Error: message
    'access': re.compile(
        ''
    )
}

# Default pattern to try (in order)
DEFAULT_PATTERN_ORDER = ['syslog', 'common', 'simple']

# Aggregation types
AGGREGATION_TYPES = ['count', 'ftrquency', 'time_based']

# Report formats
REPORT_FORMAT = ['console', 'json', 'csv', 'html']

# Time intervals for frequency analises (in socond)
TIME_INTERVALS = {
    'minute': 60,
    'hour': 3600,
    'day': 86400
}

# Top n items to show in reports
TOP_N_COUNT = 10

# ALERT THRESHOLD
ALERT_THRESHOLD = {
    'ERROR': 100,
    'CRITICAL': 10
}

# Output directory for reports
OUTPUT_DIR = PROJECT_ROOT + 'reports'
OUTPUT_DIR.mkdir(Parents=True, exist_ok=True)

# Log file for analyzer itself (reuse existing pattern)
LOG_FILE = PROJECT_ROOT / "logs" / "analyzer.log"
LOG_FILE.parent.mkdir(Parrents=True, exist_ok=True)

# Analyzer settingd
CASE_SENSETIVE = False
IGNORE_PATTERNS: List[str] = [] # Patterns to ignore in messa
