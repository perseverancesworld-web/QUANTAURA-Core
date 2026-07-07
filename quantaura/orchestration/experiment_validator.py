"""Experiment Validator - validates experiment configurations before execution."""

import logging
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ValidationError:
    """Represents a validation error."""
    field: str
    message: str
    severity: str = "error"  # error, warning, info


class ExperimentValidator:
    """Validates experiment configurations and dependencies."""
    
    def __init__(self):
        self.validators: Dict[str, Callable] = {}
        self._register_default_validators()
    
    def _register_default_validators(self):
        """Register default validation rules."""
        self.register_validator("name", self._validate_name)
        self.register_validator("task", self._validate_task)
        self.register_validator("dependencies", self._validate_dependencies)
        self.register_validator("timeout", self._validate_timeout)
        self.register_validator("retries", self._validate_retries)
        self.register_validator("priority", self._validate_priority)
    
    def register_validator(self, field: str, validator: Callable):
        """Register a custom validator function."""
        self.validators[field] = validator
    
    def _validate_name(self, name: Any) -> Optional[ValidationError]:
        """Validate experiment name."""
        if not isinstance(name, str):
            return ValidationError("name", "Name must be a string")
        if len(name) == 0:
            return ValidationError("name", "Name cannot be empty")
        if len(name) > 255:
            return ValidationError("name", "Name cannot exceed 255 characters")
        return None
    
    def _validate_task(self, task: Any) -> Optional[ValidationError]:
        """Validate experiment task."""
        if not callable(task):
            return ValidationError("task", "Task must be callable")
        return None
    
    def _validate_dependencies(self, dependencies: Any) -> Optional[ValidationError]:
        """Validate dependencies list."""
        if not isinstance(dependencies, list):
            return ValidationError("dependencies", "Dependencies must be a list")
        for dep in dependencies:
            if not isinstance(dep, str):
                return ValidationError("dependencies", "Each dependency must be a string (experiment ID)")
        return None
    
    def _validate_timeout(self, timeout_seconds: Any) -> Optional[ValidationError]:
        """Validate timeout."""
        if not isinstance(timeout_seconds, (int, float)):
            return ValidationError("timeout_seconds", "Timeout must be a number")
        if timeout_seconds <= 0:
            return ValidationError("timeout_seconds", "Timeout must be positive")
        if timeout_seconds > 86400:  # 24 hours
            return ValidationError(
                "timeout_seconds",
                "Timeout cannot exceed 24 hours",
                severity="warning"
            )
        return None
    
    def _validate_retries(self, retries: Any) -> Optional[ValidationError]:
        """Validate retry count."""
        if not isinstance(retries, int):
            return ValidationError("retries", "Retries must be an integer")
        if retries < 0:
            return ValidationError("retries", "Retries cannot be negative")
        if retries > 10:
            return ValidationError(
                "retries",
                "Retries exceeds recommended maximum",
                severity="warning"
            )
        return None
    
    def _validate_priority(self, priority: Any) -> Optional[ValidationError]:
        """Validate priority."""
        if not isinstance(priority, int):
            return ValidationError("priority", "Priority must be an integer")
        if priority < -100 or priority > 100:
            return ValidationError("priority", "Priority must be between -100 and 100")
        return None
    
    def validate_experiment(self, experiment_data: Dict) -> List[ValidationError]:
        """Validate complete experiment configuration."""
        errors = []
        
        required_fields = ["name", "task"]
        for field in required_fields:
            if field not in experiment_data:
                errors.append(ValidationError(field, f"Missing required field: {field}"))
        
        for field, value in experiment_data.items():
            if field in self.validators:
                error = self.validators[field](value)
                if error:
                    errors.append(error)
        
        return errors
    
    def validate_dependency_graph(self, experiments: Dict) -> List[ValidationError]:
        """Validate experiment dependency graph for cycles."""
        errors = []
        
        # Build adjacency list
        graph = {exp_id: [] for exp_id in experiments}
        for exp_id, exp_data in experiments.items():
            for dep in exp_data.get("dependencies", []):
                if dep not in graph:
                    errors.append(
                        ValidationError(
                            "dependencies",
                            f"Dependency '{dep}' not found in experiments"
                        )
                    )
                else:
                    graph[exp_id].append(dep)
        
        # Check for cycles using DFS
        visited = set()
        rec_stack = set()
        
        def has_cycle(node):
            visited.add(node)
            rec_stack.add(node)
            
            for neighbor in graph.get(node, []):
                if neighbor not in visited:
                    if has_cycle(neighbor):
                        return True
                elif neighbor in rec_stack:
                    return True
            
            rec_stack.remove(node)
            return False
        
        for exp_id in graph:
            if exp_id not in visited:
                if has_cycle(exp_id):
                    errors.append(
                        ValidationError("dependencies", "Circular dependency detected")
                    )
                    break
        
        return errors
    
    def format_errors(self, errors: List[ValidationError]) -> str:
        """Format validation errors for logging."""
        if not errors:
            return "No validation errors"
        
        lines = []
        for error in errors:
            lines.append(f"[{error.severity.upper()}] {error.field}: {error.message}")
        
        return "\n".join(lines)
