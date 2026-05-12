# pylint: disable=broad-except
# pylint: disable=import-outside-toplevel
#!/venv/bin/python3
"""
File scanning and categorization module for File Organizer scanner.
Handle directory sccanning, file categorization, and statistics collection.
"""

import os
from pathlib import Path
from typing import List, Dict
from datetime import datetime

# Import from local modules
try:
    from .config import LOG_FILE, FILE_CATEGORIES, IGNORED_EXTENSIONS, OTHER_CATEGORY
    from .logger import log_info, log_debug, log_warning, log_error
except ImportError:
    from config import LOG_FILE, FILE_CATEGORIES, IGNORED_EXTENSIONS, OTHER_CATEGORY
    from logger import log_info, log_debug, log_warning, log_error


def scan_directory(directory: Path, recursive: bool=True) -> List[Path]:
    """
    Scan a directory and return list of all files paths.

    Args:
        directory (Path): Path to directory to scan.
        recursive (bool, optional): If True, scan subdirectories recursively.

    Returns:
        List[Path]: List of Path objects for all files found.
    """
    log_info(f"Scanning directory: {directory}")

    if not directory.exists():
        log_error(f"Directory doesn't exist: {directory}")
        return []

    if not directory.is_dir():
        log_error(f"Path is not a directory: {directory}")
        return []

    files = []

    try:
        if recursive:
            # Find all files recursively
            for file_path in directory.rglob('*'):
                if file_path.is_file():
                    files.append(file_path)
        else:
            # Find only top level files
            for file_path in directory.iterdir():
                if file_path.is_file():
                    files.append(file_path)

        log_debug(f"Find {len(files)} files in {directory}")
        return files

    except PermissionError as e:
        log_error(f"Permission error when scanning {directory}: {e}")
        return []
    except Exception as e:
        log_error(f"Error scanning {directory}: {e}")
        return []


def get_file_extension(file_path: Path) -> str:
    """
    Extract file extension (lowercase with dot).

    Args:
        file_path (Path): Path to file

    Returns:
        str: Extension string (e.g. .pdf) or empty string if no extension
    """
    extension = file_path.suffix.lower()

    # Handle double extensions like .tar.gz
    if extension == '.gz' and file_path.stem.endswith('.tar'):
        return '.tar.gz'

    return extension


def categorize_file(file_path: Path) -> str:
    """
    Determine category for file base on its extension.

    Args:
        file_path (Path): Path to file.

    Returns:
        str: Category name (e.g. 'Images', 'Documents', 'Others')
    """
    extension = get_file_extension(file_path=file_path)

    # Check if extension should be ignored
    if extension in IGNORED_EXTENSIONS:
        log_debug(f"Ignoring file {file_path.name} (extension {extension} ignored.)")

    # Lookup category from mapping
    category = FILE_CATEGORIES.get(extension, OTHER_CATEGORY)

    log_debug(f"Categorized {file_path.name}: {extension} -> {category}")
    return category


def is_hidden_file(file_path: Path) -> bool:
    """
    Check if file is hidden (Unix hidden files, Windows hidden attribute).

    Args:
        file_path (Path): Path to file.

    Returns:
        bool: True if file is hidden, Flase otherwise.
    """
    # Check Unix hidden files (start with dot)
    if file_path.name.startswith('.'):
        return True

    # Check Windows hidden attribute (require ctype, optional)
    if os.name == 'nt': # Windows
        try:
            import ctypes
            file_attribute_hidden = 0x2
            attrs = ctypes.windll.kernel32.GetFileAttributeW(str(file_path))
            if attrs != -1 and (attrs & file_attribute_hidden):
                return True

        except(ImportError, AttributeError):
            pass # Silently fail on non-Windows or missing ctype

    return False


def get_file_stats(file_paths: List[Path]) -> Dict:
    """
    Calculate statistics about files (counts by category, total size).

    Args:
        file_paths (List[Path]): list file paths

    Returns:
        Dictionary containing:
            - 'total_files': Total number of files
            - 'total_size': Total size of bytes
            - 'catefories': Dict of category -> count
            - 'extensions': Dict of extension -> count
            - 'hidden_count': Number of hidden files
            - 'ignored_count': Number of ignored files
    """
    stats = {
        'total_files': len(file_paths), 
        'total_size': 0,
        'categories': {},
        'extensions': {},
        'hidden_count': 0,  
        'ignored_count': 0,
        'excluded_count':0
    }

    for file_path in file_paths:
        # Check hidden files
        if is_hidden_file(file_path):
            stats['hidden_count'] += 1

        # Get file size
        try:
            file_size = file_path.stat().st_size
            stats['total_size'] += file_size

        except OSError:
            log_warning(f"Could not get size for: {file_path}")

        # Get extentsion and category
        extension = get_file_extension(file_path)
        if extension:
            stats['extensions'][extension] = stats['extensions'].get(extension, 0) + 1

        # Check if ignored
        if extension in IGNORED_EXTENSIONS:
            stats['ignored_count'] += 1
            continue

        # Count by Category
        category = categorize_file(file_path)
        stats['categories'][category] = stats['categories'].get(category, 0) + 1

    log_debug(f"Statistics {stats['total_files']} files, {stats['total_size'] / (1024*1024):.1f} MB total")

    return stats


def filter_organizable_files(
        file_paths: List[Path],
        include_hidden: bool=False,
        include_ignored: bool=False
) -> List[Path]:
    """
    Filter files ot only those that should be orgenized.

    Args:
        file_paths (List[Path]): List of file paths
        include_hidden (bool, optional): If True include hidden files.
        include_ignored (bool, optional): If True include ignored extensions.

    Returns:
        List[Path]: List of files to orgenize.
    """
    filtered = []

    for file_path in file_paths:
        # Skip hidden files unless explicitly included
        if not include_hidden and is_hidden_file(file_path):
            log_debug(f"Skipping hidden file: {file_path}")
            continue

        # Skip ignored extensions unless explicitly included
        extension = get_file_extension(file_path)
        if not include_ignored and extension in IGNORED_EXTENSIONS:
            log_debug(f"Skipping ignored extension: {file_path}")
            continue

        filtered.append(file_path)

    log_info(f"Filtered {len(file_paths)} files -> {len(filtered)} orgenizable files.")
    return filtered


def group_by_category(file_paths: list[Path]) -> Dict[str, List[Path]]:
    """
    Group files by their category.

    Args:
        file_paths (list[Path]): List of file paths

    Returns:
        Dict[str, List[Path]]: Dictionary mappling category name to list of file paths 
    """
    groups = {}

    for file_path in file_paths:
        category = categorize_file(file_path)
        if category:
            groups.setdefault(category, []).append(file_path)

        else:
            # File with no category (e.g. ignored) are not gouped
            pass

    # Sort files within each category alphabetically
    for category, file_list in groups.items():
        file_list.sort(key=lambda p: p.name.lower())

    log_debug(f"Grouped into {len(groups)} categories.")
    return groups


def find_empty_folders(directory: Path, recursive: bool=True) -> List[Path]:
    """
    Finf all empty folders inside a directory.

    Args:
        directory (Path): Base directory to scan.
        recursive (bool, optional): If True, check subdirectories recursively.

    Returns:
        List[Path]: List of empty filder paths.
    """
    empty_folders = []

    if not directory.exists() or not directory.is_dir():
        return empty_folders

    try:
        if recursive:
            for folder_path in directory.rglob('*'):
                if folder_path.is_dir() and not any(folder_path.iterdir()):
                    empty_folders.append(folder_path)
        else:
            for folder_path in directory.iterdir():
                if folder_path.is_dir() and not any(folder_path.iterdir()):
                    empty_folders.append(folder_path)
    except PermissionError:
        pass

    return empty_folders


def get_directory_summary(directory: Path) -> Dict:
    """
    Get a summary of directory contents before organization.

    Args:
        directory (Path): Path of directory.

    Returns:
        Dict: Dictionary with summary information
    """
    files = scan_directory(directory, recursive=True)
    stats = get_file_stats(files)

    summary = {
        'directory': str(directory),
        'scan_time': datetime.now().isoformat(),
        'stats': stats,
        'top_categories': sorted(stats['categories'].items(), key=lambda x: x[1], reverse=True)[:5],
    }

    return summary


# Quick test (add to bottom of scanner.py temporarily)
if __name__ == "__main__":
    # For standalone execution
    try:
        from .logger import LoggerManager  # When imported as module
    except ImportError:
        from logger import LoggerManager    # When run directly

    LoggerManager.setup_logger(verbose=True, log_file=LOG_FILE)

    logger = LoggerManager.get_logger()

    # Test scanning
    test_dir = Path(".")
    files1 = scan_directory(test_dir)
    print(f"Found {len(files1)} files")

    # Test categorization
    for f in files1[:5]:
        cat = categorize_file(f)
        print(f"{f.name} → {cat}")

    # Test stats
    stats1 = get_file_stats(files1)
    print(f"Categories: {stats1['categories']}")
