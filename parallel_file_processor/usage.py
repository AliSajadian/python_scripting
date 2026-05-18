# Example usage of FileHandler with ParallelFileProcessor

try:
    from .parallel_processor import ParallelFileProcessor, ProcessingConfig
    from .file_handler import FileHandler
except ImportError:
    from parallel_processor import ParallelFileProcessor, ProcessingConfig
    from file_handler import FileHandler

def advanced_file_processing():
    """Example showing FileHandler integration"""

    # Initialize components
    file_handler = FileHandler()
    config = ProcessingConfig(max_workers=4)
    processor = ParallelFileProcessor(config)

    # 1. Get file information before processing
    file_info = file_handler.get_file_info("large_data.txt")
    print(f"Processing file: {file_info['name']} ({file_info['size_mb']:.2f} MB)")
    print(f"File hash: {file_info['md5_hash']}")

    # 2. Create backup before processing
    backup_path = file_handler.backup_file("large_data.txt")
    print(f"File backup with size: {len(backup_path)}, is created")

    # 3. Define processing function
    def process_text_chunk(content, chunk_id=None, **kwargs):
        lines = content.split('\n')
        return {
            'chunk_id': chunk_id,
            'line_count': len(lines),
            'char_count': len(content)
        }

    # 4. Process file in chunks
    results = processor.process_chunks(
        large_file="large_data.txt",
        processing_func=process_text_chunk,
        chunk_size=1024 * 1024  # 1MB chunks
    )

    # 5. Save results
    output_data = {
        'source_file': "large_data.txt",
        'total_chunks': len(results),
        'chunk_results': results
    }

    file_handler.write_json(output_data, "processing_results.json")

    # 6. Merge results if needed
    # file_handler.merge_files(["output1.txt", "output2.txt"], "merged_output.txt")

    return results

if __name__ == "__main__":
    advanced_file_processing()
