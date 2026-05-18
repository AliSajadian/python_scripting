# pylint: disable=broad-except
# pylint: disable=import-outside-toplevel
"""
Main parallel file processor with multiprocessing and multithreading support
"""
import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
from typing import List, Callable, Any, Dict, Optional
from dataclasses import dataclass
from tqdm import tqdm
import psutil

try:
    from .file_handler import FileHandler
    from .task_manager import TaskManager
    from .metrics import MetricsCollector
    from .logger import log_warning, log_error, log_info
except ImportError:
    from file_handler import FileHandler
    from task_manager import TaskManager
    from metrics import MetricsCollector
    from logger import log_warning, log_error, log_info


@dataclass
class ProcessingConfig:
    """Configuration for parallel processing"""
    max_workers: int = mp.cpu_count()
    use_processes: bool = True
    chunk_size: int = 1000
    memory_limit_gb: float = 4.0
    show_progress: bool = True

class ParallelFileProcessor:
    """
    Main class for parallel file processing
    Supports both process-based and thread-based parallelism
    """

    def __init__(self, config: ProcessingConfig = None):
        self.config = config or ProcessingConfig()
        self.metrics = MetricsCollector()
        self.task_manager = TaskManager()
        self.file_handler = FileHandler()

        # Adjust worker count based on memory
        self._adjust_workers_by_memory()

    def _adjust_workers_by_memory(self):
        """Dynamically adjust worker count based on available memory"""
        available_memory_gb = psutil.virtual_memory().available / (1024**3)

        if available_memory_gb < self.config.memory_limit_gb:
            suggested_workers = max(1, self.config.max_workers // 2)
            log_warning(f"Low memory ({available_memory_gb:.1f}GB). Reducing workers from "
                          f"{self.config.max_workers} to {suggested_workers}")
            self.config.max_workers = suggested_workers

    def process_files(self,
                     input_paths: List[str],
                     processing_func: Callable,
                     output_dir: Optional[str] = None,
                     **func_kwargs) -> Dict[str, Any]:
        """
        Process multiple files in parallel
        
        Args:
            input_paths: List of file paths to process
            processing_func: Function to apply to each file
            output_dir: Optional directory for outputs
            **func_kwargs: Additional arguments for processing_func
            
        Returns:
            Dictionary with results and metrics
        """
        self.metrics.start_timer()
        results = {}

        # Filter existing files
        valid_files = self.file_handler.filter_existing_files(input_paths)
        log_info(f"Processing {len(valid_files)} files with {self.config.max_workers} workers")

        # Choose executor
        executor_class = ProcessPoolExecutor if self.config.use_processes else ThreadPoolExecutor

        with executor_class(max_workers=self.config.max_workers) as executor:
            # Submit tasks
            future_to_file = {}
            for file_path in valid_files:
                future = executor.submit(
                    self._process_single_file,
                    file_path, processing_func, output_dir, func_kwargs
                )
                future_to_file[future] = file_path

            # Collect results with progress bar
            iterator = as_completed(future_to_file)
            if self.config.show_progress:
                iterator = tqdm(iterator, total=len(valid_files), desc="Processing files")

            for future in iterator:
                file_path = future_to_file[future]
                try:
                    result = future.result(timeout=60)
                    results[file_path] = result
                    self.metrics.record_success(file_path)
                except Exception as e:
                    error_msg = f"Failed to process {file_path}: {str(e)}"
                    log_error(error_msg)
                    results[file_path] = {'error': error_msg}
                    self.metrics.record_failure(file_path)

        self.metrics.stop_timer()
        self._print_summary()

        return results

    def _process_single_file(self,
                            file_path: str,
                            processing_func: Callable,
                            output_dir: Optional[str],
                            kwargs: Dict) -> Any:
        """
        Wrapper for processing a single file with metrics tracking
        
        Args:
            file_path: Path to file
            processing_func: Processing function
            output_dir: Output directory
            kwargs: Additional arguments
            
        Returns:
            Processing result
        """
        import time
        start_time = time.time()

        try:
            # Read file
            file_content = self.file_handler.read_file(file_path)

            # Process content
            result = processing_func(file_content, file_path=file_path, **kwargs)

            # Save output if directory provided
            if output_dir and result:
                output_path = self.file_handler.write_output(
                    result, file_path, output_dir
                )
                result['output_path'] = output_path

            execution_time = time.time() - start_time
            result['execution_time'] = execution_time

            return result

        except Exception as e:
            log_error(f"Error in _process_single_file for {file_path}: {str(e)}")
            raise

    def process_chunks(self,
                      large_file: str,
                      processing_func: Callable,
                      chunk_size: int = None) -> List[Any]:
        """
        Process a large file in parallel chunks
        
        Args:
            large_file: Path to large file
            processing_func: Function to process each chunk
            chunk_size: Size of each chunk in bytes or lines
            
        Returns:
            List of processing results for each chunk
        """
        chunk_size = chunk_size or self.config.chunk_size

        # Split file into chunks
        chunks = self.file_handler.split_file(large_file, chunk_size)
        log_info(f"Split {large_file} into {len(chunks)} chunks")

        # Process chunks in parallel
        results = []

        with ProcessPoolExecutor(max_workers=self.config.max_workers) as executor:
            futures = [
                executor.submit(processing_func, chunk, chunk_id=i)
                for i, chunk in enumerate(chunks)
            ]

            for future in tqdm(as_completed(futures), total=len(futures),
                              desc="Processing chunks"):
                results.append(future.result())

        return results

    def _print_summary(self):
        """Print processing summary"""
        summary = self.metrics.get_summary()
        log_info("=" * 50)
        log_info("Processing Summary:")
        log_info(f"  Total files: {summary['total_files']}")
        log_info(f"  Successful: {summary['successful']}")
        log_info(f"  Failed: {summary['failed']}")
        log_info(f"  Success rate: {summary['success_rate']:.2f}%")
        log_info(f"  Total time: {summary['total_time_seconds']:.2f} seconds")
        log_info("=" * 50)
