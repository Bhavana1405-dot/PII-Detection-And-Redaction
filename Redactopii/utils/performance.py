"""
Tracks performance metrics for redaction operations
"""
import time
import psutil

class PerformanceMonitor:
    """Tracks time and memory usage"""

    def __init__(self):
        self.start_time = None
        self.start_memory = None

    def start(self):
        """Begins tracking"""
        self.start_time = time.time()
        self.start_memory = psutil.Process().memory_info().rss

    def stop(self) -> dict:
        """Stops tracking and returns performance metrics"""
        end_time = time.time()
        end_memory = psutil.Process().memory_info().rss

        return {
            "execution_time_sec": round(end_time - self.start_time, 3),
            "memory_used_MB": round((end_memory - self.start_memory) / (1024 * 1024), 3)
        }
