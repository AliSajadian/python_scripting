"""
Convert csv file to json format.
Usage: python csv_to_json.py --input file.csv --output file.json
"""

import csv
import json
from pathlib import Path
from typing import Any, List, Dict, Optional

from .log_config import get_logger
from .validators import validate_file_exists, validate_output_directory


logger = get_logger(__name__)


def detect_csv_dialect(file_path: Path, sample_size: int = 1024) -> type[csv.Dialect]:
    """
    Automatically detect CSV dialect (delimiter, quote character, etc.).
    
    Args:
        file_path: Path to CSV file
        sample_size: Number of bytes to read for detection
        
    Returns:
        Detected CSV dialect
    """
    with open(file_path, 'r', encoding='utf-8') as csvfile:
        sample = csvfile.read(sample_size)
        csvfile.seek(0)
        dialect = csv.Sniffer().sniff(sample)
        logger.debug("Detected CSV dialect - delimiter: %s, quotechar: %s ",
                     dialect.delimiter, dialect.quotechar)
        return dialect


def read_csv_file(
        file_path: Path, 
        delimiter: Optional[str] = None,
        encoding: str = 'utf-8'
) -> List[Dict[str, Any]]:
    """
    Read CSV file and return list of dictionaries.

    Args:
        file_path: Path to the CSV file.

    Output:
        file_path: List of dictionaries where each dict represents a row
        delimiter: CSV delimiter (auto-detect if None)
        encoding: File encoding

    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If CSV has no headers or is empty
        csv.Error: If CSV parsing fails
    """
    # Validate file exists
    validate_file_exists(file_path)

    data: List[Dict[str, Any]] = []
    logger.info("Reading CSV file: %s", file_path)

    try:
        with open(file_path, "r", encoding=encoding) as csvfile:
            # Detect dialect if delimiter not specified
            if delimiter is None:
                dialect = detect_csv_dialect(file_path=file_path)
            else:
                dialect = csv.excel()
                dialect.delimiter = delimiter

            reader = csv.DictReader(csvfile, dialect=dialect)

            # Validate headers
            if not reader.fieldnames:
                raise ValueError("CSV file have no headers")

            logger.debug("Found CSV columns: %s", reader.fieldnames)

            for _, row in enumerate(reader, start=2):
                # Filter out empty rows
                if any(row.values()):
                    data.append(dict(row))

            # Validate data was read
            if not data:
                raise ValueError("CSV file contains no data rows")

            logger.info("Successfully read %s rows from %s columns.",
                        len(data), len(reader.fieldnames))
            return data

    except csv.Error as e:
        logger.error("CSV parsing error in %s: %s", file_path, e)
        raise
    except UnicodeDecodeError as e:
        logger.error("Encoding error in %s: %s", file_path, e)
        raise


def convert_csv_to_json(data: List[Dict[str, str]]) -> str:
    """
    Convert data list to formatted JSON string.

    Args:
        data: List of dictionaries of CSV.

    Returns:
        JSON string with identation.
    """
    logger.info("Converting data to JSON format")

    try:
        json_output = json.dumps(data, indent=2, ensure_ascii=False)
        logger.debug("JSON size %s bytes", len(json_output))
        return json_output

    except (TypeError, ValueError) as e:
        logger.error("JSON conversion error: %s", e)
        return ""


def write_to_json_file(
    data: List[Dict[str, Any]],
    output_path: Path,
    encoding: str = 'utf-8',
    indent: int = 2,
    ensure_ascii: bool = False
) -> bool:
    """
Write data to JSON file.
    
    Args:
        data: List of dictionaries to write
        output_path: Path to output JSON file
        indent: JSON indentation level
        ensure_ascii: If False, write Unicode characters as-is
        
    Returns:
        True if successful, False otherwise
    """
    logger.info("Writting JSON to file: %s", output_path)

    try:
        # Ensure output directory exists
        validate_output_directory(output_path)

        # Write JSON file
        with open(output_path, "w", encoding=encoding) as jsonfile:
            json.dump(
                data,
                jsonfile,
                indent=indent,
                ensure_ascii=ensure_ascii,
                sort_keys=True
            )

        logger.info("Successfully wrote %s records to %s", len(data), output_path)
        return True

    except IOError as e:
        logger.error("Failed to write json file %s: %s", output_path, e)
        return False
