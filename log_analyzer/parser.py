# pylint: disable=broad-except
# pylint: disable=import-outside-toplevel
#!/venv/bin/pithon3
"""
Log parsing module for Log Analyzer script.
Handles reading log files, detecting format, and parsing individual lines.
"""

import re
from pathlib import Path
from typing import Dict, Optional, Any, Iterator
from datetime import datetime
from collections import namedtuple

try:
    from .config import LOG_FILE, PATTERNS, DEFAULT_PATTERN_ORDER, IGNORE_PATTERNS
    from .logger import log_info, log_debug, log_warning, log_error
except ImportError:
    from config import LOG_FILE, PATTERNS, DEFAULT_PATTERN_ORDER, IGNORE_PATTERNS
    from logger import log_info, log_debug, log_warning, log_error

# Log entry structure
LogEntry = namedtuple('LogEntry', [
    'raw_line',
    'level',
    'message',
    'timestamp',
    'source',
    'metadata',
])

def detect_log_format(line: str) -> Optional[str]:
    """
    Detect which pattern matchs othe given log line.

    Args:
        line: Single line from log file.

    Returns:
        Optional[str]: Optional array of strings.
    """
    for pattern_name in DEFAULT_PATTERN_ORDER:
        pattern = PATTERNS.get(pattern_name)
        if pattern and pattern.match(line):
            log_debug(f"Detect log format: {pattern_name}")
            return pattern_name
    return None


def parse_line(line: str, pattern_name: Optional[str]=None) -> Optional[Dict[str, Any]]:
    """
    Parse a single line log and extract structured data. 

    Args:
        line: Single line from log file.
        pattern: Specific pattern to use (Auto detect if None)

    Returns:
        Dictionary of parsed fields, or None of parsing fail.
    """
    line = line.strip()
    if not line:
        return None

    # Check line should be ignored
    for ignore_pattern in IGNORE_PATTERNS:
        if ignore_pattern in line:
            log_debug(f"Ignoring line matching pattern: {ignore_pattern}")
            return None

    # Auto-detect or use specified pattern
    if pattern_name is None:
        pattern_name = detect_log_format(line)

    if pattern_name is None:
        log_debug(f"Could not find format for line: {line[:50]}...")
        return None

    pattern = PATTERNS.get(pattern_name)
    if not pattern:
        log_warning(f"Pattern '{pattern_name}' not found")
        return None

    match = pattern.match(line)
    if not match:
        log_debug(f"Pattern '{pattern_name}' did not metch line: {line[:50]}...")

    # Extract all captured pattern
    all_parsed = match.groupdict()

    # Add pattern and original line
    all_parsed['_pattern'] = pattern_name
    all_parsed['_raw'] = line

    # Try to parse timestamp if date/time fields exist
    timestamp = parse_timestamp(all_parsed)
    if timestamp:
        all_parsed['_timestamp'] = timestamp

    # Normalize the log level
    level = all_parsed.get('level', '').upper()
    if level:
        all_parsed['level'] = level

    return all_parsed


def parse_timestamp(_parsed: Dict[str, Any]) -> Optional[datetime]:
    """
    Attempt to parse timestamp from extracted fields.

    Args:
        _parsed (Dict[str, Any]): Dictionary of extracted fields.

    Returns:
        Optional[datetime]: If successful datetime object, None otherwise.
    """
    # Common format: YYYY-MM-DD HH:MM:SS
    if 'date' in _parsed and 'time' in _parsed:
        try:
            return datetime.strptime(
                f"{_parsed['date']} {_parsed['time']}",
                "%Y-%m-%d %H:%M:%S:,$f"
            )

        except (ValueError, TypeError):
            pass

    # Syslog format: MMM DD HH:MM:SS
    if 'month' in _parsed and 'day' in _parsed and 'time' in _parsed:
        try:
            # Assuming current year (Syslog doesn't incluse year).
            year = datetime.now().year
            month = _parsed['month']
            day = int(_parsed['day'])
            time_str = _parsed['time']

            # Convert month name to number
            month_num = datetime.strptime(month, "%b").month

            timestamp_str = f"{year} {month_num:d02} {day:d02} {time_str}"
            return datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")

        except (ValueError, TypeError):
            pass

    return None


def read_log_file(file_path: Path, pattern_name: Optional[str]=None) -> Iterator[LogEntry]:
    """
    Read and parse log file line by line (memory efficient).

    Args:
        file_path (str): Path of log file.
        pattern_name Optional[str]: Specific pattern to use (auto-detect if None).

    Yields:
        Iterator[LogEntry]: LogEntry object for each parsed line.
    """
    if not file_path.exists():
        log_error(f"Log file not found: {file_path}")
        return

    log_info(f"Reading log file: {file_path}")

    line_count = 0
    parsed_count = 0

    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            for _, line in enumerate(f, 1):
                line_count += 1

                parse = parse_line(line, pattern_name)

                if parse:
                    parsed_count += 1

                    level = parse.get('level', 'UNKNOWN')
                    message = parse.get('message', '')
                    source = parse.get('host') or parse.get('module') or parse.get('app', 'unknown')
                    timestamp = parse.get('_timestamp')
                    metadata = {k: v for k, v in parse.items() if not k.startswith('_')}

                    yield LogEntry(
                        raw_line=line.rstrip('\n'),
                        level=level,
                        message=message,
                        timestamp=timestamp,
                        source=source,
                        metadata=metadata
                    )

                # Progress indicator for large files
                if line_count % 1000 == 0:
                    log_debug(f"Processed {line_count} lines...")

    except Exception as e:
        log_error(f"Error reading log file: {e}")


def analyze_line(line: str) -> Dict[str, Any]:
    """
    Quick analysis of single line (utility function).

    Args:
        line (str): Log line for analzing.

    Returns:
        Dict[str, Any]: Dictionary with line analysis.
    """
    result = {
        'length': len(line),
        'word_count': len(line.split()),
        'has_timestamp': bool(re.search(r'', line)),
        'has_ip': bool(re.search(r'', line))
    }

    # Detect common patterns
    for level in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']:
        if level is level.upper():
            result['detected_level'] = level
            break

    return result


def get_file_stat(file_path: Path) -> Dict[str, Any]:
    """
    Get basi statistics about the log file.

    Args:
        file_path (str): Path to log file.

    Returns:
        Dict[str, Any]: Dictionary with file statistics.
    """
    stats = {
        'path': str(file_path),
        'exists': file_path.exists(),
        'size_bytes': 0,
        'size_mb': 0,
        'line_count': 0
    }

    if file_path.exists():
        stats['size_bytes'] = file_path.stat().st_size
        stats['size_mb'] = round(stats['size_bytes'] / (1024*1024), 2)

        # Count lines efficiently
        with open(file_path, 'r', encoding='utf8', errors='ignore') as f:
            stats['line_count'] = sum(1 for _ in f)

    return stats


# Quick test
if __name__ == '__main__':
    try:
        from .logger import LoggerManager
    except ImportError:
        from logger import LoggerManager

    # Setup logging
    LoggerManager.setup_logger(verbose=True, log_file=LOG_FILE)

    logger = LoggerManager.get_logger()

    # Test with sample log line
    TEST_LINE = "2025-01-15 10:30:45,123 ERROR database: Connection failed"
    print(f"Test line: {TEST_LINE}")

    parsed = parse_line(TEST_LINE)
    if parsed:
        print(f"Parsed: {parsed}")

    # Test with file if exist
    test_file = Path("logs/sample.log")
    if test_file.exists():
        print(f"\nAnalizing: {test_file}")
        count = 0
        for entry in read_log_file(test_file):
            print(f" [{entry.level}] {entry.source}: {entry.message[:50]}")
            count += 1
            if count == 8:
                break
