# pylint: disable=broad-except
# pylint: disable=import-outside-toplevel
#!/venv/bin/python3
"""
File moving and organization module for File Organizer script.
Handle create folder structure, moving files, and conflict resolution.
"""

import shutil
from pathlib import Path
from typing import List, Dict, Optional, Tuple

try:
    from .config import ALWAYS_CREATE_FOLDERS, CONFLICT_RESOLUTION, DRY_RUN_BY_DEFAULT
    from .logger import log_debug, log_error, log_info, log_warning
except ImportError:
    from config import ALWAYS_CREATE_FOLDERS, CONFLICT_RESOLUTION, DRY_RUN_BY_DEFAULT
    from logger import log_debug, log_error, log_info, log_warning


def create_category_folders(base_path: Path, categories: List[str]) -> Dict[str, Path]:
    """
    Create folders for each category.
    
    Args:
        base_path: Base directory where folders will be created
        categories: List of category names to create folders for
    
    Returns:
        Dictionary mapping category name to folder path
    """
    folder_paths = {}

    for category in categories:
        folder_path = base_path / category
        try:
            folder_path.mkdir(parents=True, exist_ok=True)
            folder_paths[category] = folder_path
            log_debug(f"Created/verified folder: {folder_path}")

        except PermissionError as e:
            log_error(f"Cannot create folder {folder_path}: {e}")
        except Exception as e:
            log_error(f"Unexpected error creating {folder_path}: {e}")

    log_info(f"Created/verified {len(folder_paths)} category folders")
    return folder_paths


def get_unique_filename(dest_path: Path) -> Path:
    """
    Generate a unique filename if file already exists.
    
    Args:
        dest_path: Desired destination path
    
    Returns:
        Unique path with number suffix if needed
    """
    if not dest_path.exists():
        return dest_path
    
    stem = dest_path.stem
    suffix = dest_path.suffix
    parent = dest_path.parent
    
    counter = 1
    while True:
        new_name = f"{stem}_{counter}{suffix}"
        new_path = parent / new_name
        if not new_path.exists():
            log_debug(f"Renamed conflict: {dest_path.name} → {new_name}")
            return new_path
        counter += 1


def move_file(
    src_path: Path,
    dest_dir: Path,
    conflict_resolution: str = CONFLICT_RESOLUTION,
    dry_run: bool = DRY_RUN_BY_DEFAULT
) -> Tuple[bool, Optional[str]]:
    """
    Move a single file to destination directory.
    
    Args:
        src_path: Source file path
        dest_dir: Destination directory
        conflict_resolution: How to handle conflicts ('rename', 'overwrite', 'skip')
        dry_run: If True, simulate without actual moving
    
    Returns:
        Tuple of (success, message)
    """
    dest_path = dest_dir / src_path.name

    # Check for conflicts
    if dest_path.exists():
        if conflict_resolution == 'rename':
            dest_path = get_unique_filename(dest_path)
        elif conflict_resolution == 'overwrite':
            log_debug(f"Will overwrite existing file: {dest_path}")
        elif conflict_resolution == 'skip':
            log_info(f"Skipping {src_path.name} (already exists)")
            return False, f"Skipped: {src_path.name} already exists"
        else:
            log_warning(f"Unknown conflict resolution '{conflict_resolution}', using 'rename'")
            dest_path = get_unique_filename(dest_path)

    try:
        if dry_run:
            log_debug(f"[DRY RUN] Would move {src_path} → {dest_path}")
            return True, f"Would move: {src_path.name}"

        # Actually move the file
        shutil.move(str(src_path), str(dest_path))
        log_debug(f"Moved: {src_path.name} → {dest_dir.name}")
        return True, f"Moved: {src_path.name}"

    except PermissionError as e:
        error_msg = f"Permission denied moving {src_path.name}: {e}"
        log_error(error_msg)
        return False, error_msg
    except Exception as e:
        error_msg = f"Error moving {src_path.name}: {e}"
        log_error(error_msg)
        return False, error_msg


def organize_files(
    grouped_files: Dict[str, List[Path]],
    base_path: Path,
    conflict_resolution: str = CONFLICT_RESOLUTION,
    dry_run: bool = DRY_RUN_BY_DEFAULT,
    create_always_folders: bool = True
) -> Dict:
    """
    Organize files by moving them to category folders.
    
    Args:
        grouped_files: Dictionary mapping category to list of file paths
        base_path: Base directory where category folders will be created
        conflict_resolution: How to handle naming conflicts
        dry_run: If True, simulate without actual moving
        create_always_folders: If True, create folders even if no files
    
    Returns:
        Dictionary with organization statistics:
            - 'moved': Number of files moved
            - 'failed': Number of files failed
            - 'skipped': Number of files skipped
            - 'folders_created': List of created folders
            - 'details': List of individual results
    """
    # Determine which categories need folders
    categories_with_files = list(grouped_files.keys())
    categories_to_create = set(categories_with_files)

    if create_always_folders:
        categories_to_create.update(ALWAYS_CREATE_FOLDERS)

    # Create folders
    folders = create_category_folders(base_path, list(categories_to_create))

    stats = {
        'moved': 0,
        'failed': 0,
        'skipped': 0,
        'folders_created': list(folders.keys()),
        'details': []
    }

    for category, file_paths in grouped_files.items():
        if category not in folders:
            log_warning(f"No folder for category '{category}', skipping {len(file_paths)} files")
            stats['skipped'] += len(file_paths)
            continue

        dest_dir = folders[category]

        for src_path in file_paths:
            success, message = move_file(
                src_path,
                dest_dir,
                conflict_resolution,
                dry_run
            )

            stats['details'].append({
                'file': str(src_path),
                'category': category,
                'success': success,
                'message': message
            })

            if success:
                stats['moved'] += 1
            else:
                stats['failed'] += 1

    log_info(f"Organization complete: {stats['moved']} moved, "
             f"{stats['failed']} failed, {stats['skipped']} skipped")

    return stats


def organize_by_category(
    base_path: Path,
    categories: Dict[str, List[Path]],
    conflict_resolution: str = CONFLICT_RESOLUTION,
    dry_run: bool = DRY_RUN_BY_DEFAULT
) -> Dict:
    """
    Organize files directly using category mapping.
    
    Args:
        file_paths: List of file paths (for statistics)
        base_path: Base directory for organizing
        categories: Dictionary mapping category to list of file paths
        conflict_resolution: How to handle conflicts
        dry_run: If True, simulate without moving
    
    Returns:
        Statistics dictionary
    """
    return organize_files(categories, base_path, conflict_resolution, dry_run)


def cleanup_empty_folders(
    directory: Path,
    dry_run: bool = DRY_RUN_BY_DEFAULT,
    recursive: bool = True
) -> List[Path]:
    """
    Remove empty folders in the directory.
    
    Args:
        directory: Base directory to clean
        dry_run: If True, simulate without deleting
        recursive: If True, remove nested empty folders
    
    Returns:
        List of removed folder paths
    """
    removed_folders = []

    if not directory.exists() or not directory.is_dir():
        return removed_folders

    # Collect empty folders
    empty_folders = []

    if recursive:
        # Need to process from deepest to shallowest
        for folder_path in sorted(directory.rglob('*'), reverse=True):
            if folder_path.is_dir() and not any(folder_path.iterdir()):
                empty_folders.append(folder_path)
    else:
        for folder_path in directory.iterdir():
            if folder_path.is_dir() and not any(folder_path.iterdir()):
                empty_folders.append(folder_path)

    # Remove empty folders
    for folder_path in empty_folders:
        if dry_run:
            log_debug(f"[DRY RUN] Would remove empty folder: {folder_path}")
            removed_folders.append(folder_path)
        else:
            try:
                folder_path.rmdir()
                log_debug(f"Removed empty folder: {folder_path}")
                removed_folders.append(folder_path)
            except OSError as e:
                log_warning(f"Cannot remove {folder_path}: {e}")

    if removed_folders:
        log_info(f"Removed {len(removed_folders)} empty folders")

    return removed_folders


def rollback_moves(move_log: List[Dict]) -> int:
    """
    Rollback previously moved files (useful for testing or error recovery).
    
    Args:
        move_log: List of move operation details (from organize_files stats['details'])
    
    Returns:
        Number of successful rollbacks
    """
    rollback_count = 0

    for entry in move_log:
        if not entry['success']:
            continue

        # Extract destination path from message (simplified)
        # In real implementation, store source/dest pairs during move
        log_warning("Rollback requires stored source/destination pairs")

    return rollback_count


def get_organization_summary(stats: Dict) -> Dict:
    """
    Generate summary dictionary from organization statistics.
    
    Args:
        stats: Statistics from organize_files()
    
    Returns:
        Summary dictionary with totals by category
    """
    summary = {
        'total_moved': stats['moved'],
        'total_failed': stats['failed'],
        'total_skipped': stats['skipped'],
        'folders_used': stats['folders_created'],
        'success_rate': 0
    }

    total = stats['moved'] + stats['failed'] + stats['skipped']
    if total > 0:
        summary['success_rate'] = (stats['moved'] / total) * 100

    return summary
