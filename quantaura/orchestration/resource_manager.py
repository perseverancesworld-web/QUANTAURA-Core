"""Resource Manager - tracks and enforces resource limits for experiments."""

import logging
import psutil
from dataclasses import dataclass
from typing import Dict, Optional
from enum import Enum

logger = logging.getLogger(__name__)


class ResourceUnit(str, Enum):
    """Units for resource quantities."""
    MB = "MB"
    GB = "GB"
    PERCENT = "%"
    CORES = "cores"


@dataclass
class ResourceConfig:
    """Resource allocation configuration for experiments."""
    max_memory_mb: int = 2048
    max_cpu_percent: float = 80.0
    max_disk_usage_mb: int = 10000
    timeout_seconds: int = 3600
    
    def to_dict(self) -> Dict:
        return {
            "max_memory_mb": self.max_memory_mb,
            "max_cpu_percent": self.max_cpu_percent,
            "max_disk_usage_mb": self.max_disk_usage_mb,
            "timeout_seconds": self.timeout_seconds,
        }


class ResourceMonitor:
    """Monitors current system resource usage."""
    
    @staticmethod
    def get_memory_usage_mb() -> float:
        """Get current process memory usage in MB."""
        process = psutil.Process()
        return process.memory_info().rss / 1024 / 1024
    
    @staticmethod
    def get_cpu_percent() -> float:
        """Get current process CPU usage percentage."""
        process = psutil.Process()
        return process.cpu_percent(interval=0.1)
    
    @staticmethod
    def get_system_memory_available_mb() -> float:
        """Get available system memory in MB."""
        return psutil.virtual_memory().available / 1024 / 1024
    
    @staticmethod
    def get_system_cpu_count() -> int:
        """Get number of CPU cores available."""
        return psutil.cpu_count()


class ResourceManager:
    """Manages resource allocation and enforcement for experiments."""
    
    def __init__(self, default_config: Optional[ResourceConfig] = None):
        self.default_config = default_config or ResourceConfig()
        self.experiment_resources: Dict[str, Dict] = {}
        self.monitor = ResourceMonitor()
    
    def allocate_resources(self, exp_id: str, config: Optional[ResourceConfig] = None) -> bool:
        """Allocate resources for experiment. Returns True if allocation succeeded."""
        config = config or self.default_config
        
        # Check if system has enough resources
        available_memory = self.monitor.get_system_memory_available_mb()
        if available_memory < config.max_memory_mb:
            logger.warning(
                f"Insufficient memory: available {available_memory:.0f}MB, "
                f"requested {config.max_memory_mb}MB"
            )
            return False
        
        self.experiment_resources[exp_id] = {
            "config": config,
            "allocated_at": __import__("datetime").datetime.utcnow().isoformat(),
            "peak_memory_mb": 0,
            "peak_cpu_percent": 0,
        }
        
        logger.info(f"Allocated resources for experiment {exp_id}: {config.to_dict()}")
        return True
    
    def release_resources(self, exp_id: str) -> Dict:
        """Release resources for experiment and return usage stats."""
        if exp_id not in self.experiment_resources:
            return {}
        
        stats = self.experiment_resources.pop(exp_id)
        logger.info(
            f"Released resources for experiment {exp_id}. "
            f"Peak memory: {stats['peak_memory_mb']:.1f}MB, "
            f"Peak CPU: {stats['peak_cpu_percent']:.1f}%"
        )
        return stats
    
    def check_resource_limits(self, exp_id: str) -> tuple[bool, str]:
        """Check if experiment is within resource limits. Returns (within_limits, reason)."""
        if exp_id not in self.experiment_resources:
            return True, "No allocation"
        
        allocation = self.experiment_resources[exp_id]
        config = allocation["config"]
        
        current_memory = self.monitor.get_memory_usage_mb()
        allocation["peak_memory_mb"] = max(allocation["peak_memory_mb"], current_memory)
        
        if current_memory > config.max_memory_mb:
            return False, f"Memory limit exceeded: {current_memory:.1f}MB > {config.max_memory_mb}MB"
        
        current_cpu = self.monitor.get_cpu_percent()
        allocation["peak_cpu_percent"] = max(allocation["peak_cpu_percent"], current_cpu)
        
        if current_cpu > config.max_cpu_percent:
            return False, f"CPU limit exceeded: {current_cpu:.1f}% > {config.max_cpu_percent}%"
        
        return True, "Within limits"
    
    def get_resource_usage(self, exp_id: str) -> Dict:
        """Get current resource usage for experiment."""
        if exp_id not in self.experiment_resources:
            return {}
        
        allocation = self.experiment_resources[exp_id]
        return {
            "config": allocation["config"].to_dict(),
            "peak_memory_mb": allocation["peak_memory_mb"],
            "peak_cpu_percent": allocation["peak_cpu_percent"],
            "current_memory_mb": self.monitor.get_memory_usage_mb(),
            "current_cpu_percent": self.monitor.get_cpu_percent(),
        }
    
    def get_system_status(self) -> Dict:
        """Get overall system resource status."""
        return {
            "available_memory_mb": self.monitor.get_system_memory_available_mb(),
            "cpu_cores": self.monitor.get_system_cpu_count(),
            "active_experiments": len(self.experiment_resources),
            "experiments": {
                exp_id: self.get_resource_usage(exp_id)
                for exp_id in self.experiment_resources
            }
        }
