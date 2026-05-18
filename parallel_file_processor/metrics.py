"""
Performance metrics collection and reporting
"""
import time
from collections import defaultdict
from typing import Dict, Any
from dataclasses import dataclass
from datetime import datetime

@dataclass
class FileMetrics:
    """Metrics for individual file processing"""
    file_path: str
    start_time: float
    end_time: float = 0
    success: bool = False
    error_message: str = ""
    size_bytes: int = 0
    processing_time: float = 0

class MetricsCollector:
    """Collects and aggregates processing metrics"""

    def __init__(self):
        self.file_metrics: Dict[str, FileMetrics] = {}
        self.start_time = None
        self.end_time = None
        self._stats = defaultdict(int)

    def start_timer(self):
        """Start overall processing timer"""
        self.start_time = time.time()

    def stop_timer(self):
        """Stop overall processing timer"""
        self.end_time = time.time()

    def start_file(self, file_path: str, size_bytes: int = 0):
        """Start tracking metrics for a file"""
        self.file_metrics[file_path] = FileMetrics(
            file_path=file_path,
            start_time=time.time(),
            size_bytes=size_bytes
        )

    def record_success(self, file_path: str):
        """Record successful file processing"""
        if file_path in self.file_metrics:
            metrics = self.file_metrics[file_path]
            metrics.end_time = time.time()
            metrics.success = True
            metrics.processing_time = metrics.end_time - metrics.start_time
            self._stats['successful'] += 1
        self._stats['total_files'] += 1

    def record_failure(self, file_path: str, error: str = ""):
        """Record failed file processing"""
        if file_path in self.file_metrics:
            metrics = self.file_metrics[file_path]
            metrics.end_time = time.time()
            metrics.success = False
            metrics.error_message = error
            metrics.processing_time = metrics.end_time - metrics.start_time
            self._stats['failed'] += 1
        self._stats['total_files'] += 1

    def get_summary(self) -> Dict[str, Any]:
        """Get processing summary"""
        successful = self._stats.get('successful', 0)
        failed = self._stats.get('failed', 0)
        total = successful + failed

        summary = {
            'total_files': total,
            'successful': successful,
            'failed': failed,
            'success_rate': (successful / total * 100) if total > 0 else 0,
            'total_time_seconds': (self.end_time - self.start_time) if self.end_time else 0,
            'average_processing_time': self._calculate_avg_time(),
            'throughput_files_per_sec': self._calculate_throughput(),
        }

        return summary

    def _calculate_avg_time(self) -> float:
        """Calculate average processing time per file"""
        times = [m.processing_time for m in self.file_metrics.values() if m.processing_time > 0]
        return sum(times) / len(times) if times else 0

    def _calculate_throughput(self) -> float:
        """Calculate processing throughput (files/second)"""
        total_time = self.end_time - self.start_time if self.end_time else 0
        if total_time > 0:
            return len(self.file_metrics) / total_time
        return 0

    def get_performance_report(self) -> str:
        """Generate detailed performance report"""
        summary = self.get_summary()

        report = f"""
Performance Report
{'='*60}
Timestamp: {datetime.now()}
Total Files: {summary['total_files']}
Successful: {summary['successful']}
Failed: {summary['failed']}
Success Rate: {summary['success_rate']:.2f}%
Total Time: {summary['total_time_seconds']:.2f} seconds
Average Processing Time: {summary['average_processing_time']:.3f} seconds/file
Throughput: {summary['throughput_files_per_sec']:.2f} files/second

Slowest Files (top 5):
"""
        # Get slowest files
        sorted_metrics = sorted(
            self.file_metrics.values(),
            key=lambda x: x.processing_time,
            reverse=True
        )[:5]

        for metrics in sorted_metrics:
            report += f"  - {metrics.file_path}: {metrics.processing_time:.2f}s\n"

        return report
