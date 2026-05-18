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

# Default log Format string
LOG_OUTPUT_FORMAT = 'common'  # Change this to switch formats

# Format string mappings
LOG_FORMATS = {
    'syslog': {
        'format': '%(asctime)s %(hostname)s %(name)s[%(process)d]: %(levelname)s - %(message)s',
        'datefmt': '%b %d %H:%M:%S'
    },
    'common': {
        'format': '%(asctime)s,%(msecs)03d %(levelname)s %(name)s: %(message)s',
        'datefmt': '%Y-%m-%d %H:%M:%S'
    },
    'simple': {
        'format': '%(levelname)s: %(message)s',
        'datefmt': None
    },
    'custom': {
        'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        'datefmt': '%Y-%m-%d %H:%M:%S'
    },
    'access': {
        'format': '%(remote_addr)s - %(remote_user)s [%(asctime)s] "%(request)s" %(status)s %(body_bytes_sent)s',
        'datefmt': '%d/%b/%Y:%H:%M:%S %z'
    }
}

# Regex patterns for common log format
PATTERNS: Dict[str, Pattern] = {
    # Standard syslog format: 16 May 01:10:30 server app[1234]: message
    'syslog': re.compile(
        r'(?P<month>\w{3})\s+(?P<day>\d{1,2})\s+(?P<time>\d{2}:\d{2}:\d{2})\s+'
        r'(?P<host>\S+)\s+(?P<app>\S+?)(?:\[(?P<pid>\d+)\])?:\s+(?P<message>.*)'
    ),

    # Common log format: 2026-05-16 01:10:30, 123 ERROR module: message
    'commomn': re.compile(
        r'(?P<date>\d{4}-\d{2}-\d{2})\s+(?P<time>\d{2}:\d{2}:\d{2},\d{3})\s+'
        r'(?P<level>[A-Z]+)\s+(?P<module>\S+):\s+(?P<message>.*)'
    ),

    # Simple format: Error: message
    'simple': re.compile(r'^(?P<level>[A-Z]+):\s+(?P<message>.*)$'),

    # Apache/Nginx access log
    'access': re.compile(
        r'(?P<ip>\S+)\s+\S+\s+\S+\s+\[(?P<time>[^\]]+)\]\s+'
        r'"(?P<method>[A-Z]+)\s+(?P<path>\S+)[^"]*"\s+'
        r'(?P<status>\d{3})\s+(?P<size>\d+)'
    ),

    # Your custom format: 2026-05-12 22:22:24 - module - LEVEL - message
    'custom': re.compile(
        r'(?P<date>\d{4}-\d{2}-\d{2})\s+(?P<time>\d{2}:\d{2}:\d{2})\s+-\s+'
        r'(?P<module>\S+)\s+-\s+(?P<level>[A-Z]+)\s+-\s+(?P<message>.*)'
    ),
}

# Default pattern to try (in order)
DEFAULT_PATTERN_ORDER = ['custom', 'syslog', 'common', 'simple']

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
OUTPUT_DIR = PROJECT_ROOT / "reports"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Log file for analyzer itself (reuse existing pattern)
LOG_FILE = PROJECT_ROOT / "logs" / "analyzer.log"
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

# Analyzer settingd
CASE_SENSETIVE = False
IGNORE_PATTERNS: List[str] = [] # Patterns to ignore in messa
