# pylint: disable=broad-except
# pylint: disable=import-outside-toplevel
"""
Task queue and dependency management
"""
# from queue import PriorityQueue
from typing import Dict, List, Any, Callable, Set
from dataclasses import dataclass, field
from enum import Enum
# import hashlib

try:
    from .logger import log_info
except ImportError:
    from logger import log_info


class TaskStatus(Enum):
    """
    Task status enumiration

    Args:
        Enum (_type_): _description_
    """
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass(order=True)
class PrioritizedTask:
    """Task with priority for queue ordering"""
    priority: int
    task_id: str = field(compare=False)
    func: Callable = field(compare=False)
    args: tuple = field(compare=False)
    kwargs: dict = field(compare=False)
    dependencies: Set[str] = field(default_factory=set, compare=False)

class TaskManager:
    """
    Manages task execution with dependency resolution and prioritization
    """

    def __init__(self):
        self.tasks: Dict[str, PrioritizedTask] = {}
        self.results: Dict[str, Any] = {}
        self.status: Dict[str, TaskStatus] = {}
        self.dependency_graph: Dict[str, Set[str]] = {}

    def add_task(self,
                task_id: str,
                func: Callable,
                args: tuple = (),
                kwargs: dict = None,
                dependencies: List[str] = None,
                priority: int = 5) -> str:
        """
        Add a task to the manager
        
        Args:
            task_id: Unique task identifier
            func: Function to execute
            args: Positional arguments
            kwargs: Keyword arguments
            dependencies: List of task IDs that must complete first
            priority: Task priority (1=highest, 10=lowest)
            
        Returns:
            Task ID
        """
        if task_id in self.tasks:
            raise ValueError(f"Task {task_id} already exists")

        kwargs = kwargs or {}
        dependencies = dependencies or []

        task = PrioritizedTask(
            priority=priority,
            task_id=task_id,
            func=func,
            args=args,
            kwargs=kwargs,
            dependencies=set(dependencies)
        )

        self.tasks[task_id] = task
        self.status[task_id] = TaskStatus.PENDING
        self.dependency_graph[task_id] = set(dependencies)

        return task_id

    def add_batch(self, tasks: List[Dict]) -> List[str]:
        """
        Add multiple tasks at once
        
        Args:
            tasks: List of task dictionaries with keys: task_id, 
            func, args, kwargs, dependencies, priority
            
        Returns:
            List of task IDs
        """
        task_ids = []
        for task_config in tasks:
            task_id = self.add_task(**task_config)
            task_ids.append(task_id)
        return task_ids

    def get_ready_tasks(self) -> List[PrioritizedTask]:
        """
        Get tasks that are ready to execute (all dependencies completed)
        
        Returns:
            List of ready tasks sorted by priority
        """
        ready = []

        for task_id, task in self.tasks.items():
            if self.status[task_id] != TaskStatus.PENDING:
                continue

            # Check if all dependencies are completed
            deps_completed = all(
                self.status.get(dep) == TaskStatus.COMPLETED
                for dep in task.dependencies
            )

            if deps_completed:
                ready.append(task)

        # Sort by priority (lower number = higher priority)
        ready.sort(key=lambda x: x.priority)
        return ready

    def execute_task(self, task: PrioritizedTask) -> Any:
        """
        Execute a single task
        
        Args:
            task: Task to execute
            
        Returns:
            Task result
        """
        try:
            self.status[task.task_id] = TaskStatus.RUNNING

            # Pass results of dependencies if needed
            kwargs = task.kwargs.copy()
            if 'dependency_results' in kwargs:
                dep_results = {
                    dep_id: self.results.get(dep_id)
                    for dep_id in task.dependencies
                }
                kwargs['dependency_results'] = dep_results

            result = task.func(*task.args, **kwargs)

            self.results[task.task_id] = result
            self.status[task.task_id] = TaskStatus.COMPLETED

            return result

        except Exception:
            self.status[task.task_id] = TaskStatus.FAILED
            raise

    def execute_all(self, max_concurrent: int = 4) -> Dict[str, Any]:
        """
        Execute all tasks respecting dependencies
        
        Args:
            max_concurrent: Maximum number of concurrent tasks
            
        Returns:
            Dictionary of task results
        """
        from concurrent.futures import ThreadPoolExecutor, as_completed

        with ThreadPoolExecutor(max_workers=max_concurrent) as executor:
            futures = {}

            while len([s for s in self.status.values() \
                       if s == TaskStatus.COMPLETED]) < len(self.tasks):
                ready_tasks = self.get_ready_tasks()

                # Submit ready tasks
                for task in ready_tasks:
                    if task.task_id not in futures:
                        future = executor.submit(self.execute_task, task)
                        futures[future] = task.task_id

                # Check for completed futures
                for future in as_completed(futures.copy()):
                    task_id = futures.pop(future)
                    try:
                        task_result = future.result()
                        log_info(f"Task {task_id} completed successfully \
                                 with result: {task_result}")
                        print(f"Task {task_id} completed successfully")
                    except Exception as e:
                        print(f"Task {task_id} failed: {str(e)}")

        return self.results
# pylint: disable=import-outside-toplevel

    def get_task_status(self, task_id: str = None) -> Dict:
        """
        Get status of tasks
        
        Args:
            task_id: Specific task ID, or None for all tasks
            
        Returns:
            Status dictionary
        """
        if task_id:
            return {
                'task_id': task_id,
                'status': self.status.get(task_id, TaskStatus.PENDING).value,
                'result': self.results.get(task_id),
                'dependencies': list(self.dependency_graph.get(task_id, []))
            }
        return {
            task_id: {
                'status': status.value,
                'completed': status == TaskStatus.COMPLETED
            }
            for task_id, status in self.status.items()
        }

    def clear(self):
        """Clear all tasks and results"""
        self.tasks.clear()
        self.results.clear()
        self.status.clear()
        self.dependency_graph.clear()
