# pylint: disable=broad-except
"""
Custom worker pool for fine-grained control over parallel processing
"""
import multiprocessing as mp
from queue import Queue
from typing import List, Callable, Any, Optional
from threading import Thread
import signal
import time

try:
    from .logger import log_warning, log_debug, log_info
except ImportError:
    from logger import log_warning, log_debug, log_info


class WorkerPool:
    """
    Custom worker pool with task queue and result collection
    Supports both process and thread workers
    """

    def __init__(self,
                 num_workers: int = None,
                 worker_type: str = 'process'):
        """
        Initialize worker pool
        
        Args:
            num_workers: Number of worker processes/threads
            worker_type: 'process' or 'thread'
        """
        self.num_workers = num_workers or mp.cpu_count()
        self.worker_type = worker_type
        self.task_queue = Queue()
        self.result_queue = Queue()
        self.workers = []
        self.is_running = False

    def start(self, worker_func: Callable):
        """
        Start the worker pool
        
        Args:
            worker_func: Function that workers will execute
        """
        self.is_running = True

        for i in range(self.num_workers):
            if self.worker_type == 'process':
                worker = mp.Process(
                    target=self._worker_loop,
                    args=(worker_func, i),
                    daemon=True
                )
            else:
                worker = Thread(
                    target=self._worker_loop,
                    args=(worker_func, i),
                    daemon=True
                )

            worker.start()
            self.workers.append(worker)
            log_debug(f"Started {self.worker_type} worker {i}")

    def _worker_loop(self, worker_func: Callable, _worker_id: int):
        """
        Main worker loop
        
        Args:
            worker_func: Function to execute for each task
            worker_id: Worker identifier
        """
        signal.signal(signal.SIGINT, signal.SIG_IGN)

        while self.is_running:
            try:
                # Get task with timeout to check is_running periodically
                task = self.task_queue.get(timeout=1)

                if task is None:  # Poison pill
                    break

                task_id, args, kwargs = task

                try:
                    result = worker_func(*args, **kwargs)
                    self.result_queue.put((task_id, result, None))
                except Exception as e:
                    self.result_queue.put((task_id, None, str(e)))

            except Exception:
                continue

    def submit(self, task_id: Any, *args, **kwargs):
        """
        Submit a task to the pool
        
        Args:
            task_id: Unique identifier for the task
            *args, **kwargs: Arguments for worker function
        """
        self.task_queue.put((task_id, args, kwargs))

    def get_results(self, timeout: Optional[float] = None) -> List[tuple]:
        """
        Collect all results from the queue
        
        Args:
            timeout: Maximum time to wait for results
            
        Returns:
            List of (task_id, result, error) tuples
        """
        results = []
        expected_results = self.task_queue.qsize()

        start_time = time.time()

        while len(results) < expected_results:
            if timeout and (time.time() - start_time) > timeout:
                log_warning(f"Timeout waiting for results. Got {len(results)}/{expected_results}")
                break

            try:
                result = self.result_queue.get(timeout=1)
                results.append(result)
            except Exception:
                continue

        return results

    def stop(self):
        """Stop all workers"""
        self.is_running = False

        # Send poison pills
        for _ in self.workers:
            self.task_queue.put(None)

        # Wait for workers to finish
        for worker in self.workers:
            worker.join(timeout=5)

        log_info(f"Stopped {len(self.workers)} workers")

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.stop()
