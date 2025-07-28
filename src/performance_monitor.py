import time
import logging
import json
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class PerformanceMonitor:
    """
    Monitor browser startup performance and optimization effectiveness.
    """
    
    def __init__(self):
        self.cache_dir = Path("/app/.cache")
        self.metrics_file = self.cache_dir / "performance_metrics.json"
        self.metrics_file.parent.mkdir(parents=True, exist_ok=True)
        
    def start_timer(self, operation: str) -> float:
        """Start timing an operation."""
        return time.time()
    
    def end_timer(self, start_time: float, operation: str) -> float:
        """End timing an operation and log the duration."""
        duration = time.time() - start_time
        logger.info(f"{operation} completed in {duration:.2f} seconds")
        self._save_metric(operation, duration)
        return duration
    
    def _save_metric(self, operation: str, duration: float):
        """Save performance metric to file."""
        try:
            metrics = self._load_metrics()
            if operation not in metrics:
                metrics[operation] = []
            
            metrics[operation].append({
                "duration": duration,
                "timestamp": time.time()
            })
            
            # Keep only last 100 measurements
            if len(metrics[operation]) > 100:
                metrics[operation] = metrics[operation][-100:]
            
            with open(self.metrics_file, 'w') as f:
                json.dump(metrics, f, indent=2)
                
        except Exception as e:
            logger.warning(f"Failed to save performance metric: {e}")
    
    def _load_metrics(self) -> Dict[str, Any]:
        """Load existing performance metrics."""
        try:
            if self.metrics_file.exists():
                with open(self.metrics_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load performance metrics: {e}")
        
        return {}
    
    def get_average_duration(self, operation: str) -> Optional[float]:
        """Get average duration for an operation."""
        metrics = self._load_metrics()
        if operation in metrics and metrics[operation]:
            durations = [m["duration"] for m in metrics[operation]]
            return sum(durations) / len(durations)
        return None
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get a summary of all performance metrics."""
        metrics = self._load_metrics()
        summary = {}
        
        for operation, measurements in metrics.items():
            if measurements:
                durations = [m["duration"] for m in measurements]
                summary[operation] = {
                    "average": sum(durations) / len(durations),
                    "min": min(durations),
                    "max": max(durations),
                    "count": len(measurements)
                }
        
        return summary
    
    def log_performance_summary(self):
        """Log a summary of performance metrics."""
        summary = self.get_performance_summary()
        
        if summary:
            logger.info("=== Performance Summary ===")
            for operation, stats in summary.items():
                logger.info(f"{operation}:")
                logger.info(f"  Average: {stats['average']:.2f}s")
                logger.info(f"  Min: {stats['min']:.2f}s")
                logger.info(f"  Max: {stats['max']:.2f}s")
                logger.info(f"  Count: {stats['count']}")
        else:
            logger.info("No performance metrics available yet.")

# Global performance monitor instance
_performance_monitor = None

def get_performance_monitor() -> PerformanceMonitor:
    """Get the global performance monitor instance."""
    global _performance_monitor
    if _performance_monitor is None:
        _performance_monitor = PerformanceMonitor()
    return _performance_monitor

def monitor_operation(operation: str):
    """Decorator to monitor operation performance."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            monitor = get_performance_monitor()
            start_time = monitor.start_timer(operation)
            try:
                result = func(*args, **kwargs)
                monitor.end_timer(start_time, operation)
                return result
            except Exception as e:
                monitor.end_timer(start_time, f"{operation}_error")
                raise
        return wrapper
    return decorator 