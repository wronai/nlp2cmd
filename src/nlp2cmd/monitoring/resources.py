"""
Resource monitoring utilities for NLP2CMD.

Provides CPU, memory, and energy consumption tracking.
"""

import time
try:
    import psutil
except Exception:  # pragma: no cover
    class _PsutilStub:
        def cpu_percent(self, *args, **kwargs):
            return 0.0
        def Process(self, *args, **kwargs):
            class _ProcessStub:
                def memory_info(self):
                    class _MemInfo:
                        rss = 0
                    return _MemInfo()
                def memory_percent(self):
                    return 0.0
            return _ProcessStub()
    psutil = _PsutilStub()
from typing import Dict, Any, Optional
from dataclasses import dataclass
from contextlib import contextmanager


@dataclass
class ResourceMetrics:
    """Resource consumption metrics."""
    cpu_percent: float
    memory_mb: float
    memory_percent: float
    execution_time_ms: float
    energy_estimate: Optional[float] = None


class ResourceMonitor:
    """Monitor system resource usage during command execution."""
    
    def __init__(self):
        self.process = psutil.Process()
    
    def get_current_metrics(self) -> ResourceMetrics:
        """Get current resource metrics."""
        return ResourceMetrics(
            cpu_percent=psutil.cpu_percent(),
            memory_mb=self.process.memory_info().rss / 1024 / 1024,
            memory_percent=self.process.memory_percent(),
            execution_time_ms=0.0
        )
    
    @contextmanager
    def measure_execution(self):
        """Context manager to measure resource usage during execution."""
        start_time = time.time()
        start_metrics = self.get_current_metrics()
        
        # Reset CPU measurement
        psutil.cpu_percent(interval=None)
        
        try:
            yield
        finally:
            end_time = time.time()
            end_metrics = self.get_current_metrics()
            
            execution_time = (end_time - start_time) * 1000  # Convert to ms
            
            # Calculate average CPU usage during execution
            avg_cpu = psutil.cpu_percent(interval=None)
            
            # Estimate energy consumption (simplified model)
            # Energy (J) = Power (W) * Time (s)
            # Assuming average power draw based on CPU and memory usage
            power_estimate = (avg_cpu / 100) * 65 + (end_metrics.memory_percent / 100) * 10  # Watts
            energy_joules = power_estimate * (execution_time / 1000)  # Convert ms to s
            
            metrics = ResourceMetrics(
                cpu_percent=avg_cpu,
                memory_mb=end_metrics.memory_mb,
                memory_percent=end_metrics.memory_percent,
                execution_time_ms=execution_time,
                energy_estimate=energy_joules
            )
            
            # Store metrics for later access
            self.last_metrics = metrics
    
    def get_last_metrics(self) -> Optional[ResourceMetrics]:
        """Get metrics from last execution."""
        return getattr(self, 'last_metrics', None)
    
    def format_metrics(self, metrics: ResourceMetrics) -> str:
        """Format metrics for display."""
        lines = [
            f"⏱️  Time: {metrics.execution_time_ms:.1f}ms",
            f"💻 CPU: {metrics.cpu_percent:.1f}%",
            f"🧠 RAM: {metrics.memory_mb:.1f}MB ({metrics.memory_percent:.1f}%)"
        ]
        
        if metrics.energy_estimate is not None:
            if metrics.energy_estimate < 0.001:
                energy_str = f"{metrics.energy_estimate * 1000:.3f}mJ"
            elif metrics.energy_estimate < 1.0:
                energy_str = f"{metrics.energy_estimate:.3f}J"
            else:
                energy_str = f"{metrics.energy_estimate:.2f}J"
            lines.append(f"⚡ Energy: {energy_str}")
        
        return " | ".join(lines)


# Global monitor instance
_monitor = ResourceMonitor()


def get_monitor() -> ResourceMonitor:
    """Get the global resource monitor instance."""
    return _monitor


@contextmanager
def measure_resources():
    """Convenient context manager for resource measurement."""
    with _monitor.measure_execution():
        yield


def get_last_metrics() -> Optional[ResourceMetrics]:
    """Get metrics from last execution."""
    return _monitor.get_last_metrics()


def format_last_metrics() -> str:
    """Format metrics from last execution for display."""
    metrics = get_last_metrics()
    if metrics:
        return _monitor.format_metrics(metrics)
    return ""


def get_system_info() -> Dict[str, Any]:
    """Get general system information."""
    return {
        "cpu_count": psutil.cpu_count(),
        "memory_total_gb": psutil.virtual_memory().total / 1024 / 1024 / 1024,
        "platform": psutil.platform.system(),
    }
