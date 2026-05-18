# pylint: disable=broad-except
# pylint: disable=import-outside-toplevel

## 📄 `main.py` for Log Analyzer

#!/usr/bin/env python3
"""
Main entry point for Log Analyzer script.
Composes parser, aggregator, and reporter modules.
"""

import sys
from pathlib import Path
from typing import Optional

import click

try:
    from .config import (
        DEFAULT_LOG_FILE,
        TOP_N_COUNT,
        OUTPUT_DIR,
        REPORT_FORMATS,
        LOG_FILE as LOG_FILE_CONFIG
    )
    from .logger import LoggerManager, log_info, log_error
    from .parser import read_log_file, get_file_stats
    from .reporter import aggregate_stats, generate_report, generate_all_reports
except ImportError:
    from config import (
        DEFAULT_LOG_FILE,
        TOP_N_COUNT,
        OUTPUT_DIR,
        REPORT_FORMATS,
        LOG_FILE as LOG_FILE_CONFIG
    )
    from logger import LoggerManager, log_info, log_error
    from reporter import aggregate_stats, generate_report, generate_all_reports


@click.command()
@click.option('--file', '-f',
              type=click.Path(exists=True, path_type=Path),
              default=DEFAULT_LOG_FILE,
              help='Path to log file to analyze')
@click.option('--frmat', '-fmt',
              default='console',
              type=click.Choice(REPORT_FORMATS),
              help='Output format for the report')
@click.option('--output', '-o',
              type=click.Path(path_type=Path),
              default=None,
              help='Output file path (for json/csv/html formats)')
@click.option('--top', '-t',
              default=TOP_N_COUNT,
              type=int,
              help=f'Number of top items to show (default: {TOP_N_COUNT})')
@click.option('--verbose', '-v',
              is_flag=True,
              default=False,
              help='Enable verbose output')
@click.option('--all-formats', '-a',
              is_flag=True,
              default=False,
              help='Generate all report formats')
@click.option('--level', '-l',
              default=None,
              help='Filter by log level (ERROR, WARNING, INFO, DEBUG)')
@click.option('--source', '-s',
              default=None,
              help='Filter by source/module name')
def main(
    file: Path=None,
    frmat: str='',
    output: Optional[Path]=None,
    top: int=0,
    verbose: bool=True,
    all_formats: bool=True,
    level: Optional[str]=None,
    source: Optional[str]=None
) -> None:
    """
    Analyze log file and generate reports.
    
    Examples:
        python main.py -f app.log
        python main.py -f app.log --frmat json --output report.json
        python main.py -f app.log --level ERROR --top 20
        python main.py -f app.log --all-formats
    """
    # Setup logger
    log_file = LOG_FILE_CONFIG
    log_file.parent.mkdir(parents=True, exist_ok=True)
    LoggerManager.setup_logger(verbose=verbose, log_file=log_file)

    log_info(f"Starting log analyzer on: {file}")
    log_info(f"Report frmat: {frmat}")

    # Check file exists
    if not file.exists():
        log_error(f"Log file not found: {file}")
        sys.exit(1)

    # Show file stats
    stats = get_file_stats(file)
    log_info(f"File size: {stats['size_mb']} MB, Lines: {stats['line_count']}")

    try:
        # Read and parse log entries
        log_info("Parsing log file...")
        entries = read_log_file(file)

        # Apply filters if specified
        if level or source:
            entries = filter_entries(entries, level, source)

        # Aggregate statistics
        log_info("Aggregating statistics...")
        report = aggregate_stats(entries)

        # Override top N count
        report.top_errors = report.top_errors[:top]

        # Display summary
        print_summary(report)

        # Generate report
        if all_formats:
            log_info("Generating all report formats...")
            output_paths = generate_all_reports(report, "log_analysis")
            for path in output_paths:
                log_info(f"  → {path}")
        else:
            if frmat == 'console':
                generate_report(report, frmat)
            else:
                output_path = output or OUTPUT_DIR / f"log_report.{frmat}"
                generate_report(report, frmat, output_path.stem)
                log_info(f"Report saved to: {output_path}")

        log_info("Analysis complete!")

    except KeyboardInterrupt:
        log_info("Interrupted by user")
        sys.exit(1)
    except Exception as e:
        log_error(f"Unexpected error: {e}")
        if verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


def filter_entries(entries, level: Optional[str], source: Optional[str]):
    """
    Filter log entries by level and/or source.
    
    Args:
        entries: Iterator of LogEntry objects
        level: Filter by log level (e.g., 'ERROR')
        source: Filter by source/module name
    
    Yields:
        Filtered LogEntry objects
    """
    level_upper = level.upper() if level else None
    source_lower = source.lower() if source else None

    for entry in entries:
        if level_upper and entry.level != level_upper:
            continue
        if source_lower and source_lower not in entry.source.lower():
            continue
        yield entry


def print_summary(report) -> None:
    """Print quick summary before full report."""
    print("\n" + "=" * 50)
    print("📊 QUICK SUMMARY")
    print("=" * 50)
    print(f"  Total lines:    {report.total_lines}")
    print(f"  Parsed lines:   {report.parsed_lines}")
    print(f"  Failed lines:   {report.failed_lines}")
    print(f"  Unique messages: {report.unique_messages}")

    if report.level_counts:
        errors = report.level_counts.get('ERROR', 0)
        warnings = report.level_counts.get('WARNING', 0)
        critical = report.level_counts.get('CRITICAL', 0)
        print(f"  Errors:         {errors}")
        print(f"  Warnings:       {warnings}")
        print(f"  Critical:       {critical}")

    if report.top_errors:
        print(f"\n  Top error: {report.top_errors[0][0][:60]}...")
        print(f"    (occurred {report.top_errors[0][1]} times)")

    print("=" * 50 + "\n")


if __name__ == "__main__":
    main()
