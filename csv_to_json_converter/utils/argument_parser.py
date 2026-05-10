"""
Command-line argument parsing for CSV to JSON converter.
"""

import argparse
from pathlib import Path

def parse_arguments() -> argparse.Namespace:
    """
    Parse command line arguments.
    
    Returns:
        Namespace object containing parsed arguments
    """
    parser = argparse.ArgumentParser(
        description='Convert CSV file to JSON format',
        epilog='Example: python csv_to_json.py -i sample.csv -o sample.json',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        '--input', '-i',
        required=True,
        type=Path,
        help='Path to input CSV file'
    )

    parser.add_argument(
        '--output', '-o',
        required=True,
        type=Path,
        help='Path to output JSON file'
    )

    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable DEBUG logging'
    )

    parser.add_argument(
        '--delimiter', '-d',
        type=str,
        default=None,
        help='CSV delimiter (auto-detect if not specified)'
    )

    parser.add_argument(
        '--encoding', '-e',
        type=str,
        default='utf-8',
        help='File encoding (default: utf-8)'
    )

    return parser.parse_args()
