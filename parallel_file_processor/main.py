#!/usr/bin/env python3
"""
Main entry point for Parallel File Processor
"""
import sys
import argparse
from pathlib import Path
from typing import List, Dict, Any

sys.path.insert(0, str(Path(__file__).parent))

try:
    from .parallel_processor import ParallelFileProcessor, ProcessingConfig
    from .logger import log_info, log_error
except ImportError:
    from parallel_processor import ParallelFileProcessor, ProcessingConfig
    from logger import log_info, log_error


def process_text_files(file_paths: List[str], search_term: str = None):
    """Example: Process text files to count lines and search for terms"""

    def text_processor(content: str, _file_path: str = None, **kwargs) -> Dict[str, Any]:
        lines = content.split('\n')
        search_term = kwargs.get('search_term')

        _result = {
            'file': _file_path,
            'total_lines': len(lines),
            'total_chars': len(content),
        }

        if search_term:
            matching_lines = [line for line in lines if search_term.lower() in line.lower()]
            _result['search_term'] = search_term
            _result['matches'] = len(matching_lines)
            _result['matching_lines'] = matching_lines[:5]  # First 5 matches

        return _result

    config = ProcessingConfig(max_workers=4, use_processes=True)
    processor = ParallelFileProcessor(config)

    _results = processor.process_files(
        input_paths=file_paths,
        processing_func=text_processor,
        output_dir='processed_output',
        search_term=search_term
    )

    return _results

def process_large_file(_file_path: str, chunk_size: int = 1000):
    """Example: Process a large file in chunks"""

    def chunk_processor(chunk: str, chunk_id: int = None) -> Dict[str, Any]:
        lines = chunk.split('\n')
        return {
            'chunk_id': chunk_id,
            'lines': len(lines),
            'size_bytes': len(chunk.encode('utf-8'))
        }

    config = ProcessingConfig(max_workers=4)
    processor = ParallelFileProcessor(config)

    _results = processor.process_chunks(
        large_file=_file_path,
        processing_func=chunk_processor,
        chunk_size=chunk_size
    )

    return _results

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Parallel File Processor')
    parser.add_argument('--mode', choices=['files', 'large'], required=True,
                       help='Processing mode')
    parser.add_argument('--input', nargs='+', required=True,
                       help='Input file(s) to process')
    parser.add_argument('--search', default=None,
                       help='Search term for text files')
    parser.add_argument('--chunk-size', type=int, default=1000,
                       help='Chunk size for large file processing')

    args = parser.parse_args()

    if args.mode == 'files':
        results = process_text_files(args.input, search_term=args.search)

        # Print summary
        for file_path, result in results.items():
            if 'error' in result:
                log_error(f"Failed: {file_path} - {result['error']}")
            else:
                log_info(f"Success: {file_path} - {result.get('total_lines', 0)} lines")

    elif args.mode == 'large':
        results = process_large_file(args.input[0], chunk_size=args.chunk_size)

        total_lines = sum(r['lines'] for r in results)
        total_size = sum(r['size_bytes'] for r in results)
        log_info(f"Processed {len(results)} chunks: {total_lines} lines, {total_size} bytes")
