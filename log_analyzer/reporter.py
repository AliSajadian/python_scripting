# pylint: disable=broad-except
# pylint: disable=import-outside-toplevel

## 📄 `reporter.py` for Log Analyzer

#!/usr/bin/env python3
"""
Report generation module for Log Analyzer script.
Generates summaries, statistics, and formatted reports from parsed log data.
"""

import json
import csv
from pathlib import Path
from datetime import datetime
from collections import Counter
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field

try:
    from .config import TOP_N_COUNT, OUTPUT_DIR
    from .logger import log_info, log_error
except ImportError:
    from config import TOP_N_COUNT, OUTPUT_DIR
    from logger import log_info, log_error

@dataclass
class LogReport:
    """Container for log analysis results."""
    total_lines: int = 0
    parsed_lines: int = 0
    failed_lines: int = 0
    level_counts: Dict[str, int] = field(default_factory=dict)
    source_counts: Dict[str, int] = field(default_factory=dict)
    top_errors: List[Tuple[str, int]] = field(default_factory=list)
    timeline: Dict[str, int] = field(default_factory=dict)
    time_range: Tuple[Optional[datetime], Optional[datetime]] = (None, None)
    unique_messages: int = 0


def aggregate_stats(_entries) -> LogReport:
    """
    Aggregate statistics from parsed log entries.
    
    Args:
        entries: Iterator of LogEntry objects
    
    Returns:
        LogReport object with aggregated statistics
    """
    _report = LogReport()
    level_counter = Counter()
    source_counter = Counter()
    error_counter = Counter()
    timeline_counter = Counter()
    message_set = set()
    timestamps = []

    for entry in _entries:
        _report.total_lines += 1

        if entry.level:
            _report.parsed_lines += 1
            level_counter[entry.level] += 1
            source_counter[entry.source] += 1
            message_set.add(entry.message)

            # Track errors separately
            if entry.level in ('ERROR', 'CRITICAL'):
                error_counter[entry.message] += 1

            # Timeline by hour
            if entry.timestamp:
                timestamps.append(entry.timestamp)
                hour_key = entry.timestamp.strftime('%Y-%m-%d %H:00')
                timeline_counter[hour_key] += 1
        else:
            _report.failed_lines += 1

    _report.level_counts = dict(level_counter)
    _report.source_counts = dict(source_counter)
    _report.top_errors = error_counter.most_common(TOP_N_COUNT)
    _report.timeline = dict(timeline_counter)
    _report.unique_messages = len(message_set)

    if timestamps:
        _report.time_range = (min(timestamps), max(timestamps))

    log_info(f"Aggregated stats: {_report.parsed_lines} parsed, "
             f"{_report.failed_lines} failed, {_report.unique_messages} unique messages")

    return _report


def generate_console_report(_report: LogReport) -> None:
    """
    Print formatted _report to console using Rich.
    
    Args:
        _report: LogReport object with aggregated statistics
    """
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel

    console = Console()

    # Header
    console.print(Panel.fit(
        "[bold cyan]📊 LOG ANALYSIS REPORT[/bold cyan]",
        border_style="cyan"
    ))

    # Summary table
    summary_table = Table(title="📈 Summary", style="green")
    summary_table.add_column("Metric", style="cyan")
    summary_table.add_column("Value", style="white")

    summary_table.add_row("Total lines processed", str(_report.total_lines))
    summary_table.add_row("Successfully parsed", f"[green]{_report.parsed_lines}[/green]")
    summary_table.add_row("Failed to parse", f"[red]{_report.failed_lines}[/red]")
    summary_table.add_row("Unique messages", str(_report.unique_messages))

    if _report.time_range[0] and _report.time_range[1]:
        duration = _report.time_range[1] - _report.time_range[0]
        summary_table.add_row("Time range", f"{_report.time_range[0]} → {_report.time_range[1]}")
        summary_table.add_row("Duration", str(duration).split('.')[0])

    console.print(summary_table)

    # Log levels table
    if _report.level_counts:
        level_table = Table(title="📋 Log Levels", style="yellow")
        level_table.add_column("Level", style="bold")
        level_table.add_column("Count", justify="right")
        level_table.add_column("Percentage", justify="right")

        total = sum(_report.level_counts.values())
        for level, count in sorted(_report.level_counts.items()):
            pct = (count / total) * 100
            color = "red" if level in ('ERROR', 'CRITICAL') else \
                    "yellow" if level == 'WARNING' else "white"
            level_table.add_row(
                f"[{color}]{level}[/{color}]",
                str(count),
                f"{pct:.1f}%"
            )
        
        console.print(level_table)
    
    # Top sources
    if _report.source_counts:
        source_table = Table(title="🔗 Top Sources", style="blue")
        source_table.add_column("Source", style="cyan")
        source_table.add_column("Count", justify="right")
        
        for source, count in list(_report.source_counts.items())[:TOP_N_COUNT]:
            source_table.add_row(source, str(count))
        
        console.print(source_table)
    
    # Top errors
    if _report.top_errors:
        error_table = Table(title="❌ Top Errors", style="red")
        error_table.add_column("Error Message", style="dim")
        error_table.add_column("Count", justify="right")
        
        for msg, count in _report.top_errors[:TOP_N_COUNT]:
            # Truncate long messages
            short_msg = msg[:80] + "..." if len(msg) > 80 else msg
            error_table.add_row(short_msg, str(count))
        
        console.print(error_table)
    
    # Timeline (top hours)
    if _report.timeline:
        timeline_table = Table(title="⏱️ Activity Timeline (Top Hours)", style="magenta")
        timeline_table.add_column("Hour", style="cyan")
        timeline_table.add_column("Entries", justify="right")
        
        for hour, count in list(sorted(_report.timeline.items()))[-TOP_N_COUNT:]:
            timeline_table.add_row(hour, str(count))
        
        console.print(timeline_table)


def generate_json_report(_report: LogReport, output_path: Path) -> None:
    """
    Export _report as JSON file.
    
    Args:
        _report: LogReport object
        output_path: Path to save JSON file
    """
    data = {
        'summary': {
            'total_lines': _report.total_lines,
            'parsed_lines': _report.parsed_lines,
            'failed_lines': _report.failed_lines,
            'unique_messages': _report.unique_messages,
        },
        'level_counts': _report.level_counts,
        'source_counts': _report.source_counts,
        'top_errors': [{'message': msg, 'count': cnt} for msg, cnt in _report.top_errors],
        'timeline': _report.timeline,
        'time_range': {
            'start': _report.time_range[0].isoformat() if _report.time_range[0] else None,
            'end': _report.time_range[1].isoformat() if _report.time_range[1] else None
        }
    }

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    log_info(f"JSON report saved to: {output_path}")


def generate_csv_report(_report: LogReport, output_path: Path) -> None:
    """
    Export _report as CSV file.
    
    Args:
        _report: LogReport object
        output_path: Path to save CSV file
    """
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)

        # Level counts
        writer.writerow(['Log Levels'])
        writer.writerow(['Level', 'Count'])
        for level, count in sorted(_report.level_counts.items()):
            writer.writerow([level, count])

        writer.writerow([])

        # Source counts
        writer.writerow(['Top Sources'])
        writer.writerow(['Source', 'Count'])
        for source, count in list(_report.source_counts.items())[:TOP_N_COUNT]:
            writer.writerow([source, count])

        writer.writerow([])

        # Top errors
        writer.writerow(['Top Errors'])
        writer.writerow(['Error Message', 'Count'])
        for msg, count in _report.top_errors[:TOP_N_COUNT]:
            writer.writerow([msg, count])

    log_info(f"CSV report saved to: {output_path}")


def generate_html_report(_report: LogReport, output_path: Path) -> None:
    """
    Export _report as HTML file.
    
    Args:
        _report: LogReport object
        output_path: Path to save HTML file
    """
    html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Log Analysis Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        h1 {{ color: #333; }}
        h2 {{ color: #666; margin-top: 20px; }}
        table {{ border-collapse: collapse; width: 100%; margin-bottom: 20px; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #4CAF50; color: white; }}
        tr:nth-child(even) {{ background-color: #f2f2f2; }}
        .error {{ color: red; }}
        .warning {{ color: orange; }}
        .info {{ color: green; }}
    </style>
</head>
<body>
    <h1>📊 Log Analysis Report</h1>
    <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    
    <h2>Summary</h2>
    <table>
        <tr><th>Metric</th><th>Value</th></tr>
        <tr><td>Total lines processed</td><td>{_report.total_lines}</td></tr>
        <tr><td>Successfully parsed</td><td>{_report.parsed_lines}</td></tr>
        <tr><td>Failed to parse</td><td>{_report.failed_lines}</td></tr>
        <tr><td>Unique messages</td><td>{_report.unique_messages}</td></tr>
    </table>
    
    <h2>Log Levels</h2>
    <table>
        <tr><th>Level</th><th>Count</th></tr>
        {''.join(f'<tr><td class="{level.lower()}">{level}</td><td>{count}</td></tr>' 
                 for level, count in sorted(_report.level_counts.items()))}
    </table>
    
    <h2>Top Errors</h2>
    <table>
        <tr><th>Error Message</th><th>Count</th></tr>
        {''.join(f'<tr><td>{msg[:100]}</td><td>{count}</td></tr>' 
                 for msg, count in _report.top_errors[:TOP_N_COUNT])}
    </table>
</body>
</html>
    """

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)

    log_info(f"HTML report saved to: {output_path}")


def generate_report(_report: LogReport, format_type: str = 'console',
                    output_name: str = 'log_report') -> Optional[Path]:
    """
    Generate _report in specified format.
    
    Args:
        _report: LogReport object
        format_type: One of 'console', 'json', 'csv', 'html'
        output_name: Base name for output files (without extension)
    
    Returns:
        Path to output file (if file-based), None for console
    """
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    if format_type == 'console':
        generate_console_report(_report)
        return None

    elif format_type == 'json':
        output_path = OUTPUT_DIR / f"{output_name}.json"
        generate_json_report(_report, output_path)
        return output_path

    elif format_type == 'csv':
        output_path = OUTPUT_DIR / f"{output_name}.csv"
        generate_csv_report(_report, output_path)
        return output_path

    elif format_type == 'html':
        output_path = OUTPUT_DIR / f"{output_name}.html"
        generate_html_report(_report, output_path)
        return output_path

    else:
        log_error(f"Unknown format: {format_type}")
        return None


def generate_all_reports(_report: LogReport, output_name: str = 'log_report') -> List[Path]:
    """
    Generate reports in all available formats.
    
    Args:
        _report: LogReport object
        output_name: Base name for output files
    
    Returns:
        List of paths to generated files
    """
    paths = []
    for fmt in ['json', 'csv', 'html']:
        path = generate_report(_report, fmt, output_name)
        if path:
            paths.append(path)

    # Console report always displayed
    generate_console_report(_report)

    return paths


# Quick test
if __name__ == "__main__":
    try:
        from .parser import read_log_file
        from .logger import LoggerManager
    except ImportError:
        from logger import LoggerManager

    # Setup logging
    log_file = Path("logs/analyzer.log")
    log_file.parent.mkdir(parents=True, exist_ok=True)
    LoggerManager.setup_logger(verbose=True, log_file=log_file)

    # Test with sample log
    sample_log = Path("logs/sample.log")
    if sample_log.exists():
        entries = list(read_log_file(sample_log))
        report = aggregate_stats(entries)
        generate_all_reports(report, "test_report")
        print(f"\nReports saved to: {OUTPUT_DIR}")
    else:
        print(f"Sample log not found: {sample_log}")
