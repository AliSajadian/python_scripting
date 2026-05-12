# pylint: disable=broad-except
# pylint: disable=import-outside-toplevel
#!/env/bin/python3
"""
Logging configuration for file orgnizer script
provide colored console output, and structured logging support
"""

import logging
import sys
from pathlib import Path
from typing import Dict, Optional

from rich.console import Console
from rich.table import Table
from rich.progress import Progress, BarColumn, TextColumn, TimeRemainingColumn


# Attempt to import structlog for structured logging (optional)
try:
    import structlog
    from structlog.dev import ConsoleRenderer
    STRUCTLOG_AVAILABLE = True
except ImportError:
    STRUCTLOG_AVAILABLE = False

# Rich console for pretty output
console = Console()


class LoggerManager():
    """Manager of logger instance"""
    _instance: Optional[logging.Logger] = None
    _verbose: bool = False
    _log_file: Optional[Path] = None

    @classmethod
    def setup_logger(cls, verbose: bool=False, log_file: Optional[Path]=None) -> None:
        """
        Configure and return logger instance

        Args:
            verbose: If True set the logging level to DEBUG, otherwise INFO.
            log_file: Optional path to write loggs to file

        Returns:
            logging.Logger: Configure loggger instance
        """
        cls._verbose = verbose
        cls._log_file = log_file

        # Determine logging level
        level = logging.DEBUG if verbose else logging.INFO

        # Create logger
        logger = logging.getLogger('file_orgenizer')
        logger.setLevel(level=level)

        # Clear any existing handlers
        logger.handlers.clear()

        # Create formatters
        file_format = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        # Console handler (with color if available)
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level=level)
        console_handler.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
        logger.addHandler(console_handler)

        # File handler (if log_file provided)
        if log_file:
            try:
                log_file.parent.mkdir(parents=True, exist_ok=True)
                file_handler = logging.FileHandler(log_file, encoding='utf-8')
                file_handler.setLevel(logging.DEBUG)
                file_handler.setFormatter(file_format)
                logger.addHandler(file_handler)
                logger.debug("Logging to file: %s", log_file)
            except Exception as e:
                logger.warning(" %s", e)

        # Setup structlog if availabe (for structes logging)
        if STRUCTLOG_AVAILABLE and verbose:
            setup_structlog()

        cls._instance = logger

    @classmethod
    def get_logger(cls) -> logging.Logger:
        """
        Return logger instance (auto-setup with defaults if needed).

        Returns:
            logging.Logger: logger instance (call setup_logger first)
        """
        if cls._instance is None:
            # Use stored config or defaults
            cls.setup_logger(
                verbose=cls._verbose,
                log_file=cls._log_file
            )

        return cls._instance


# ===================
#  Helper Functions
# ===================
def setup_structlog() -> None:
    """Configure structlog for structed logging (used with --verbose)"""
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt='iso'),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            ConsoleRenderer()
        ],
        context_class=Dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True
    )


def log_summary(stats: dict) -> None:
    """
    Display organization summary table using rich

    Args:
        stats: Dictionary containing:
            - 'categories': Dict of category -> count
            - 'total_files': Total number of files organized
            - 'total_size': Total size in bytes
            - 'folders_created': Number of folders created
            - 'conflicts': Number of conflicts resolved
    """
    if not stats.get('show', True):
        return

    # Create main table
    table = Table(title="📊 Organization summary", style="bold cyan")
    table.add_column("Metrc", style="cyan", no_wrap=True)
    table.add_column("Value", style="green")

    # Catelog breakdown (if availabe)
    categgories = stats.get('categgories', {})
    if categgories:
        table.add_row("", "")
        table.add_row("📁  categories", "")

        # Sort descending
        sorted_cats = sorted(categgories.items, key=lambda x: x[1], reverse=True)
        for category, count in sorted_cats:
            table.add_row("  • %s", category, "%s files", count)

    # Summary totals
    table.add_row("", "")
    table.add_row("📈 Total files", str(stats.get('total_files', 0)))

    total_size = stats.get('total_size', 0)
    if total_size > 0:
        size_str = format_size(total_size)
        table.add_row("💾 Total size", size_str)

    folder_created = stats.get('folder_created', 0)
    if folder_created > 0:
        table.add_row("📁 Folder created", str(folder_created))

    conflicts = stats.get('conflicts', 0)
    if conflicts > 0:
        table.add_row("⚠️  Conflicts resolved", str(conflicts))

    dry_run = stats('dry_run', False)
    if dry_run:
        table.add_row("🎭 Mode", "[yellow]DRY RUN (no files were acually moved)[/yellow]")

    console.print(table)

    # Print warning if dry run
    if dry_run:
        console.print("[bold yellow]⚠️  This was a DRY RUN. " \
                    "No files were acually moved[/bold yellow]")
        console.print("[yellow]RUN without --dry-run to orgenize files for real.[/yellow]")


def format_size(size_bytes: int) -> str:
    """
    Convert bytes to human readable format

    Args:
        size_bytes (int): Size in bytes

    Returns:
        str: Human readable string (e.g., '2.3 MB')
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} PB"


def create_progress() -> Progress:
    """
    Create a rich progress bar for file operations

    Returns:
        Progress: Progress instance
    """
    return Progress(
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:3.0f}%"),
        TimeRemainingColumn(),
        console=console,
        transient=False
    )


def log_error(message: str, exc_info: bool=False) -> None:
    """
    Log a error message with optional exception info

    Args:
        message (str): Error message
        exc_info (bool, optional): If True include exception info
    """
    logger = LoggerManager.get_logger()
    logger.error(message, exc_info=exc_info)
    console.print(f"[red]❌  Error: {message} [/red]")


def log_warning(message: str) -> None:
    """
    Log a warning mesage

    Args:
        message (str): Warning message
    """
    logger = LoggerManager.get_logger()
    logger.warning(message)
    console.print(f"[yellow]⚠️  Warning: {message} [/yellow]")


def log_info(message: str) -> None:
    """
    Log a info message

    Args:
        message (str): Info message
    """
    logger = LoggerManager.get_logger()
    logger.info(message)
    console.print(f"[green]ℹ️  Info: {message} [/green]")


def log_debug(message: str) -> None:
    """
    Log a debug message

    Args:
        message (str): Debug message
    """
    logger = LoggerManager.get_logger()
    logger.debug(message)
    if logger.isEnabledFor(logging.DEBUG):
        console.print(f"[dim]ℹ️  Debug: {message} [/dim]")
