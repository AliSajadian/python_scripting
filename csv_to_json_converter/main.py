# pylint: disable=broad-except
# pylint: disable=import-outside-toplevel
#!/venv/bin/ python3.11

"""
Convert csv file to json format.
Usage: python csv_to_json.py --input file.csv --output file.json
"""

import sys

from utils.argument_parser import parse_arguments
from utils.log_config import setup_logging, get_logger
from utils.converter import read_csv_file, write_to_json_file
from utils.validators import validate_csv_structure


def main() -> int:
    """
    Main function to orchestrate CSV to JSON conversation.

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    try:
        # Parse arguments
        args = parse_arguments()

        # Setup logging base on verbode flag
        log_level = 'DEBUG' if args.verbose else 'INFO'
        setup_logging(log_level=log_level)

        logger = get_logger('__name__')

        logger.info("=" * 50)
        logger.info("CSV to JSON Converter Started")
        logger.info("Input file: %s", args.input)
        logger.info("Output file: %s", args.output)
        logger.info("Log level: %s", log_level)

        # Read CSV file
        data = read_csv_file(
            file_path=args.input,
            delimiter=args.delimiter,
            encoding=args.encoding
        )

        # Validate data structure
        if not validate_csv_structure(data, min_rows=1):
            logger.error("CSV data validation failed")
            return 1

        logger.debug("First row sample: %s", data[0] if data else 'No data')

        # Write JSON file
        success = write_to_json_file(data=data, output_path=args.output)

        if success:
            logger.info("Conversion completerd successfully.")
            logger.info("Output saved to %s", args.output.absolute())
            return 0

        logger.info("Failed to write JSON file!")
        return 1

    except FileNotFoundError as e:
        # Use print because logging might not be setup yet
        print("File error: %s", e, file=sys.stderr)
        return 1
    except ValueError as e:
        print("Validation error: %s", e)
        return 1
    except Exception as e:  # pylint: disable=broad-except
        print("Unexpected error: %s", e)
        import traceback
        print(traceback.format_exc())
        return 1

if __name__ == "__main__":
    sys.exit(main())
