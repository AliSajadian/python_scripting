"""
Validation utilities for file operations.
"""

import os
from pathlib import Path
from typing import List, Dict, Any

def validate_file_exists(file_path: Path) -> None:
    """
    Validate that a file exists and is readable.
    
    Args:
        file_path: Path to file to validate
        
    Raises:
        FileNotFoundError: If file doesn't exist
        PermissionError: If file exists but can't be read
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    if not file_path.is_file():
        raise ValueError(f"Path is not a file: {file_path}")

    if not os.access(file_path, os.R_OK):
        raise PermissionError(f"Cannot read file: {file_path}")

def validate_output_directory(output_path: Path) -> None:
    """
    Validate and create output directory if needed.
    
    Args:
        output_path: Path to output file
        
    Raises:
        PermissionError: If directory can't be created
    """
    output_dir = output_path.parent

    # Create directory if it doesn't exist
    if not output_dir.exists():
        output_dir.mkdir(parents=True, exist_ok=True)
        __import__('logging').getLogger(__name__).debug(f"Created directory: {output_dir}")

    # Check write permissions
    if not os.access(output_dir, os.W_OK):
        raise PermissionError(f"Cannot write to directory: {output_dir}")

def validate_csv_structure(data: List[Dict[str, Any]], min_rows: int = 1) -> bool:
    """
    Validate CSV data structure.
    
    Args:
        data: List of dictionaries from CSV
        min_rows: Minimum number of rows required
        
    Returns:
        True if valid, False otherwise
    """
    if not data:
        return False

    if len(data) < min_rows:
        return False

    # Check that all rows have same keys
    expected_keys = set(data[0].keys())
    for i, row in enumerate(data[1:], start=2):
        if set(row.keys()) != expected_keys:
            __import__('logging').getLogger(__name__).warning(
                f"Row {i} has different structure: {set(row.keys())} vs {expected_keys}"
            )
            return False

    return True
