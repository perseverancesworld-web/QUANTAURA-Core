"""Retry Policy - defines failure recovery strategies for experiments."""

import logging
import asyncio
from enum import Enum
from typing import Callable, Optional, Type
from dataclasses import dataclass

logger = logging.getLogger(__name__)


class RetryStrategy(str, Enum):
    """Retry strategies for experiment failures."""
    EXPONENTIAL_BACKOFF = "exponential_backoff"
    LINEAR_BACKOFF = "linear_backoff"
    IMMEDIATE = "immediate"
    FIXED_DELAY = "fixed_delay"


@dataclass
class RetryPolicy:
    """Defines retry behavior for failed experiments."""
    max_retries: int = 3
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL_BACKOFF
    initial_delay_seconds: float = 1.0
    max_delay_seconds: float = 300.0
    backoff_multiplier: float = 2.0
    retryable_exceptions: tuple = (Exception,)
    
    def get_delay(self, attempt: int) -> float:
        """Calculate delay before retry based on strategy and attempt number."""
        if attempt < 0:
            return 0.0
        
        if self.strategy == RetryStrategy.IMMEDIATE:
            return 0.0
        
        elif self.strategy == RetryStrategy.FIXED_DELAY:
            return self.initial_delay_seconds
        
        elif self.strategy == RetryStrategy.LINEAR_BACKOFF:
            delay = self.initial_delay_seconds * (attempt + 1)
            return min(delay, self.max_delay_seconds)
        
        elif self.strategy == RetryStrategy.EXPONENTIAL_BACKOFF:
            delay = self.initial_delay_seconds * (self.backoff_multiplier ** attempt)
            return min(delay, self.max_delay_seconds)
        
        return 0.0
    
    def should_retry(self, exception: Exception, attempt: int) -> bool:
        """Determine if exception should trigger a retry."""
        if attempt >= self.max_retries:
            return False
        
        if not isinstance(exception, self.retryable_exceptions):
            return False
        
        return True
    
    async def execute_with_retry(self, func: Callable, *args, **kwargs) -> any:
        """Execute function with automatic retry on failure."""
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                if asyncio.iscoroutinefunction(func):
                    result = await func(*args, **kwargs)
                else:
                    result = await asyncio.to_thread(func, *args, **kwargs)
                
                if attempt > 0:
                    logger.info(f"Retry succeeded on attempt {attempt + 1}")
                
                return result
            
            except Exception as e:
                last_exception = e
                
                if not self.should_retry(e, attempt):
                    logger.error(
                        f"Exception not retryable or max retries exceeded: {e}"
                    )
                    raise
                
                delay = self.get_delay(attempt)
                logger.warning(
                    f"Attempt {attempt + 1} failed with {type(e).__name__}: {e}. "
                    f"Retrying in {delay:.2f}s (max_retries={self.max_retries})"
                )
                
                await asyncio.sleep(delay)
        
        raise last_exception
