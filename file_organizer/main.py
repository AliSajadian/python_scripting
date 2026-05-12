# pylint: disable=broad-except
# pylint: disable=import-outside-toplevel
#!/venv/bin/ python3
"""
Main entry point for File Organizer script.
Composes scanner, mover, and logger modules.
"""

import sys
from pathlib import Path

import click

try:
    from .config import LOG_FILE, SHOW_STATS, CONFLICT_RESOLUTION, DRY_RUN_BY_DEFAULT, \
        DEFAULT_TARGET_DIR, VERBOSE_BY_DEFAULT
    from .logger import LoggerManager, log_error, log_info
    from .scanner import scan_directory, filter_organizable_files, group_by_category, get_file_stats
    from .mover import organize_files, cleanup_empty_folders, get_organization_summary
except ImportError:
    from config import LOG_FILE, SHOW_STATS, CONFLICT_RESOLUTION, DRY_RUN_BY_DEFAULT, \
        DEFAULT_TARGET_DIR, VERBOSE_BY_DEFAULT
    from logger import LoggerManager, log_error, log_info
    from scanner import scan_directory, filter_organizable_files, group_by_category, get_file_stats
    from mover import organize_files, cleanup_empty_folders, get_organization_summary


@click.command()
@click.option('--path', '-p', type=click.Path(exists=True, path_type=Path),
              default=DEFAULT_TARGET_DIR, help='Directory to organize')
@click.option('--dry-run', '-d', is_flag=True, default=DRY_RUN_BY_DEFAULT,
              help='Simulate without actually moving files')
@click.option('--verbose', '-v', is_flag=True, default=VERBOSE_BY_DEFAULT,
              help='Enable verbose output')
@click.option('--no-stats', is_flag=True, default=False, help='Disable summary statistics')
@click.option('--conflict', '-c', default=CONFLICT_RESOLUTION,
              type=click.Choice(['rename', 'overwrite', 'skip']),
              help='How to handle filename conflicts')
@click.option('--cleanup', is_flag=True, default=False, 
              help='Remove empty folders after organization')
def main(path: Path=DEFAULT_TARGET_DIR,
         dry_run: bool=DRY_RUN_BY_DEFAULT,
         verbose: bool=VERBOSE_BY_DEFAULT,
         no_stats: bool=False,
         conflict: str=CONFLICT_RESOLUTION,
         cleanup: bool=False
) -> None:
    """
    Organize files in the specified directory by moving them into category folders.
    """
    # Setup logger
    LoggerManager.setup_logger(verbose=verbose, log_file=LOG_FILE)

    log_info(f"Starting file organizer on: {path}")
    log_info(
        f"Mode: {'DRY RUN (no files will be moved)' if dry_run else 'LIVE (files will be moved)'}"
    )

    if dry_run:
        log_info("⚠️  Dry run mode enabled - no changes will be made")

    try:
        # Step 1: Scan directory
        log_info("Scanning directory...")
        all_files = scan_directory(path, recursive=True)

        if not all_files:
            log_info("No files found to organize")
            return

        # Step 2: Get statistics (before)
        stats_before = get_file_stats(all_files)
        log_info(
            f"Found {len(all_files)} files ({stats_before['total_size'] / (1024*1024):.1f} MB)"
        )

        # Step 3: Filter files
        organizable_files = filter_organizable_files(all_files)

        if not organizable_files:
            log_info("No organizable files found (all are hidden or ignored)")
            return

        # Step 4: Group by category
        grouped = group_by_category(organizable_files)
        log_info(f"Grouped into {len(grouped)} categories")

        # Step 5: Organize files
        stats = organize_files(
            grouped_files=grouped,
            base_path=path,
            conflict_resolution=conflict,
            dry_run=dry_run
        )

        # Step 6: Cleanup empty folders (optional)
        if cleanup and not dry_run:
            removed = cleanup_empty_folders(path, dry_run=dry_run)
            log_info(f"Removed {len(removed)} empty folders")

        # Step 7: Display summary
        if not no_stats and SHOW_STATS:
            summary = get_organization_summary(stats)
            display_stats(stats_before, stats, summary, dry_run)

        log_info("Organization complete!")

    except KeyboardInterrupt:
        log_info("Interrupted by user")
        sys.exit(1)
    except Exception as e:
        log_error(f"Unexpected error: {e}")
        sys.exit(1)


def display_stats(before: dict, move_stats: dict, summary: dict, dry_run: bool) -> None:
    """Display organization statistics."""
    print("\n" + "="*50)
    print("📊 ORGANIZATION SUMMARY")
    print("="*50)
    print(f"📁 Directory scanned: {DEFAULT_TARGET_DIR}")
    print(f"📄 Files found: {before['total_files']}")
    print(f"💾 Total size: {before['total_size'] / (1024*1024):.1f} MB")
    print(f"📦 Files organized: {move_stats['moved']}")
    print(f"⚠️  Failed/Skipped: {move_stats['failed'] + move_stats['skipped']}")
    print(f"📁 Categories created: {len(move_stats['folders_created'])}")
    print(f"📈 Success rate: {summary['success_rate']:.1f}%")

    if dry_run:
        print("\n⚠️  DRY RUN - No files were actually moved")
        print("   Run without --dry-run to organize files for real")

    print("="*50)


if __name__ == "__main__":
    main()
