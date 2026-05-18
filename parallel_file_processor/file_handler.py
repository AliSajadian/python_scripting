# pylint: disable=broad-except
# pylint: disable=import-outside-toplevel
"""
File handling utilities for reading, writing, and splitting files
"""
import json
import csv
import shutil
from pathlib import Path
from typing import List, Dict, Any, Optional, Union, Iterator
from datetime import datetime
import hashlib

try:
    from .logger import log_info, log_error, log_debug, log_warning
except ImportError:
    from logger import log_info, log_error, log_debug, log_warning


class FileHandler:
    """
    Handles file operations including reading, writing, splitting, and merging
    Supports various file formats: text, CSV, JSON, binary
    """

    def __init__(self, encoding: str = 'utf-8'):
        """
        Initialize FileHandler
        
        Args:
            encoding: Default file encoding
        """
        self.encoding = encoding
        self.supported_formats = {'.txt', '.csv', '.json', '.log', '.xml', '.html'}

    def read_file(self, file_path: str, binary: bool = False) -> Union[str, bytes]:
        """
        Read a file completely
        
        Args:
            file_path: Path to the file
            binary: Read as binary if True, else as text
            
        Returns:
            File content as string or bytes
            
        Raises:
            FileNotFoundError: If file doesn't exist
            IOError: If file can't be read
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        try:
            if binary:
                with open(file_path, 'rb') as f:
                    content = f.read()
                log_debug(f"Read binary file: {file_path} ({len(content)} bytes)")
            else:
                with open(file_path, 'r', encoding=self.encoding) as f:
                    content = f.read()
                log_debug(f"Read text file: {file_path} ({len(content)} chars)")

            return content

        except Exception as e:
            log_error(f"Failed to read file {file_path}: {str(e)}")
            raise IOError(f"Cannot read file {file_path}: {str(e)}") from e

    def read_file_lines(self, file_path: str, max_lines: Optional[int] = None) -> List[str]:
        """
        Read file line by line (memory efficient for large files)
        
        Args:
            file_path: Path to the file
            max_lines: Maximum number of lines to read (None for all)
            
        Returns:
            List of lines
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        lines = []

        try:
            with open(file_path, 'r', encoding=self.encoding) as f:
                for i, line in enumerate(f):
                    if max_lines and i >= max_lines:
                        break
                    lines.append(line.rstrip('\n'))

            log_debug(f"Read {len(lines)} lines from {file_path}")
            return lines

        except Exception as e:
            log_error(f"Failed to read lines from {file_path}: {str(e)}")
            raise IOError(f"Cannot read lines from {file_path}: {str(e)}") from e

    def read_file_chunks(self, file_path: str, chunk_size: int = 8192) -> Iterator[bytes]:
        """
        Read file in chunks (most memory efficient for very large files)
        
        Args:
            file_path: Path to the file
            chunk_size: Size of each chunk in bytes
            
        Yields:
            Chunks of file content
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        try:
            with open(file_path, 'rb') as f:
                while True:
                    chunk = f.read(chunk_size)
                    if not chunk:
                        break
                    yield chunk

        except Exception as e:
            log_error(f"Failed to read chunks from {file_path}: {str(e)}")
            raise IOError(f"Cannot read chunks from {file_path}: {str(e)}") from e

    def read_json(self, file_path: str) -> Dict[str, Any]:
        """
        Read and parse JSON file
        
        Args:
            file_path: Path to JSON file
            
        Returns:
            Parsed JSON data
        """
        content = self.read_file(file_path)

        try:
            data = json.loads(content)
            log_debug(f"Successfully parsed JSON from {file_path}")
            return data
        except json.JSONDecodeError as e:
            log_error(f"Invalid JSON in {file_path}: {str(e)}")
            raise

    def read_csv(self, file_path: str, delimiter: str = ',') -> List[Dict[str, str]]:
        """
        Read CSV file and return as list of dictionaries
        
        Args:
            file_path: Path to CSV file
            delimiter: CSV delimiter
            
        Returns:
            List of dictionaries (one per row)
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        rows = []

        try:
            with open(file_path, 'r', encoding=self.encoding) as f:
                reader = csv.DictReader(f, delimiter=delimiter)
                for row in reader:
                    rows.append(row)

            log_debug(f"Read {len(rows)} rows from CSV {file_path}")
            return rows

        except Exception as e:
            log_error(f"Failed to read CSV {file_path}: {str(e)}")
            raise

    def write_file(self, content: Union[str, bytes], file_path: str, binary: bool = False) -> str:
        """
        Write content to a file
        
        Args:
            content: Content to write
            file_path: Output file path
            binary: Write as binary if True
            
        Returns:
            Path to written file
        """
        file_path = Path(file_path)

        # Create parent directories if needed
        file_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            if binary:
                with open(file_path, 'wb') as f:
                    f.write(content)
            else:
                with open(file_path, 'w', encoding=self.encoding) as f:
                    f.write(content)

            log_info(f"Written to {file_path} ({len(content)} bytes)")
            return str(file_path)

        except Exception as e:
            log_error(f"Failed to write to {file_path}: {str(e)}")
            raise IOError(f"Cannot write to {file_path}: {str(e)}") from e

    def write_json(self, data: Any, file_path: str, indent: int = 2) -> str:
        """
        Write data as JSON file
        
        Args:
            data: Data to write
            file_path: Output file path
            indent: JSON indentation
            
        Returns:
            Path to written file
        """
        try:
            json_str = json.dumps(data, indent=indent, default=str)
            return self.write_file(json_str, file_path)
        except Exception as e:
            log_error(f"Failed to write JSON to {file_path}: {str(e)}")
            raise

    def write_csv(self, data: List[Dict[str, Any]], file_path: str,
                  fieldnames: List[str] = None) -> str:
        """
        Write list of dictionaries as CSV file
        
        Args:
            data: List of dictionaries
            file_path: Output file path
            fieldnames: Column names (uses keys from first row if None)
            
        Returns:
            Path to written file
        """
        if not data:
            log_warning(f"No data to write to {file_path}")
            return ""

        file_path = Path(file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)

        if not fieldnames:
            fieldnames = list(data[0].keys())

        try:
            with open(file_path, 'w', encoding=self.encoding, newline='') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(data)

            log_info(f"Written {len(data)} rows to CSV {file_path}")
            return str(file_path)

        except Exception as e:
            log_error(f"Failed to write CSV to {file_path}: {str(e)}")
            raise

    def write_output(self, result: Dict[str, Any], source_file: str, output_dir: str) -> str:
        """
        Write processing result to output directory
        
        Args:
            result: Processing result dictionary
            source_file: Original source file path
            output_dir: Output directory
            
        Returns:
            Path to output file
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Generate output filename from source filename
        source_path = Path(source_file)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"{source_path.stem}_processed_{timestamp}.json"
        output_path = output_dir / output_filename

        # Add metadata
        output_data = {
            'source_file': source_file,
            'processed_at': timestamp,
            'result': result
        }

        return self.write_json(output_data, str(output_path))

    def split_file(self, file_path: str, chunk_size: Union[int, str]) -> List[bytes]:
        """
        Split a file into chunks for parallel processing
        
        Args:
            file_path: Path to file to split
            chunk_size: Size of each chunk (bytes if int, or 'lines' for line-based split)
            
        Returns:
            List of file chunks (bytes)
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        chunks = []
        file_size = file_path.stat().st_size

        if isinstance(chunk_size, str) and chunk_size == 'lines':
            # Split by number of lines (balanced)
            chunks = self._split_by_lines(file_path)
        else:
            # Split by byte size
            chunk_size_bytes = int(chunk_size)
            chunks = self._split_by_bytes(file_path, chunk_size_bytes)

        log_info(f"Split {file_path} ({file_size} bytes) into {len(chunks)} chunks")
        return chunks

    def _split_by_bytes(self, file_path: Path, chunk_size: int) -> List[bytes]:
        """Split file by byte size"""
        chunks = []

        with open(file_path, 'rb') as f:
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                chunks.append(chunk)

        return chunks

    def _split_by_lines(self, file_path: Path) -> List[bytes]:
        """Split file by lines (roughly equal number of lines per chunk)"""
        # First, count total lines
        total_lines = 0
        with open(file_path, 'r', encoding=self.encoding) as f:
            total_lines = sum(1 for _ in f)

        if total_lines == 0:
            return []

        # Determine number of chunks based on CPU count
        import multiprocessing as mp
        num_chunks = mp.cpu_count()
        lines_per_chunk = max(1, total_lines // num_chunks)

        chunks = []
        current_chunk = []
        current_line_count = 0

        with open(file_path, 'r', encoding=self.encoding) as f:
            for line in f:
                current_chunk.append(line)
                current_line_count += 1

                if current_line_count >= lines_per_chunk:
                    chunks.append(''.join(current_chunk).encode(self.encoding))
                    current_chunk = []
                    current_line_count = 0

            # Add remaining lines
            if current_chunk:
                chunks.append(''.join(current_chunk).encode(self.encoding))

        return chunks

    def merge_files(self, input_files: List[str], output_file: str,
                    delete_originals: bool = False) -> str:
        """
        Merge multiple files into one
        
        Args:
            input_files: List of files to merge
            output_file: Output file path
            delete_originals: Delete input files after merging
            
        Returns:
            Path to merged file
        """
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            with open(output_path, 'wb') as outfile:
                for input_file in input_files:
                    with open(input_file, 'rb') as infile:
                        shutil.copyfileobj(infile, outfile)

            log_info(f"Merged {len(input_files)} files into {output_file}")

            if delete_originals:
                for input_file in input_files:
                    Path(input_file).unlink()
                log_debug(f"Deleted {len(input_files)} original files")

            return str(output_path)

        except Exception as e:
            log_error(f"Failed to merge files: {str(e)}")
            raise

    def filter_existing_files(self, file_paths: List[str]) -> List[str]:
        """
        Filter list to only include existing files
        
        Args:
            file_paths: List of file paths to check
            
        Returns:
            List of existing file paths
        """
        existing = []

        for file_path in file_paths:
            path = Path(file_path)
            if path.exists() and path.is_file():
                existing.append(file_path)
            else:
                log_warning(f"Skipping non-existent file: {file_path}")

        log_info(f"Found {len(existing)} existing files out of {len(file_paths)}")
        return existing

    def get_file_info(self, file_path: str) -> Dict[str, Any]:
        """
        Get detailed information about a file
        
        Args:
            file_path: Path to file
            
        Returns:
            Dictionary with file information
        """
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        stat = path.stat()

        # Calculate file hash (for deduplication)
        hash_md5 = hashlib.md5()
        with open(path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)

        info = {
            'path': str(path.absolute()),
            'name': path.name,
            'stem': path.stem,
            'suffix': path.suffix,
            'size_bytes': stat.st_size,
            'size_mb': stat.st_size / (1024 * 1024),
            'created': datetime.fromtimestamp(stat.st_ctime),
            'modified': datetime.fromtimestamp(stat.st_mtime),
            'is_text': self._is_text_file(path),
            'md5_hash': hash_md5.hexdigest(),
            'lines': self._count_lines(path) if self._is_text_file(path) else None
        }

        return info

    def _is_text_file(self, file_path: Path) -> bool:
        """Check if file is likely a text file"""
        try:
            with open(file_path, 'r', encoding=self.encoding) as f:
                f.read(1024)
            return True
        except Exception:
            return False

    def _count_lines(self, file_path: Path) -> int:
        """Count lines in text file efficiently"""
        count = 0
        with open(file_path, 'r', encoding=self.encoding) as f:
            for count, _ in enumerate(f, 1):
                pass
        return count

    def backup_file(self, file_path: str, backup_dir: str = "backups") -> str:
        """
        Create a backup of a file
        
        Args:
            file_path: Path to file to backup
            backup_dir: Backup directory
            
        Returns:
            Path to backup file
        """
        source = Path(file_path)

        if not source.exists():
            raise FileNotFoundError(f"Cannot backup: {file_path} not found")

        backup_path = Path(backup_dir)
        backup_path.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = backup_path / f"{source.stem}_backup_{timestamp}{source.suffix}"

        shutil.copy2(source, backup_file)
        log_info(f"Backed up {file_path} to {backup_file}")

        return str(backup_file)
    