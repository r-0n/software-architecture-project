"""
Retry Policy and Circuit Breaker Implementation

Provides resilience patterns for external service calls.
"""
import time
import random
import logging
from typing import List, Type, Dict, Any, Optional
from enum import Enum
from django.core.cache import cache
from retail.logging import log_breaker_transition


logger = logging.getLogger(__name__)


class CircuitBreakerState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing fast
    HALF_OPEN = "half_open"  # Testing if service recovered


class RetryPolicy:
    """
    Retry policy with exponential backoff and jitter.
    """
    
    def __init__(self, 
                 retry_on: List[Type[Exception]] = None,
                 attempts: int = 3,
                 base_delay: float = 0.2,
                 max_delay: float = 2.0,
                 jitter: float = 0.1):
        """
        Initialize retry policy.
        
        Args:
            retry_on: Exception types to retry on
            attempts: Maximum number of attempts
            base_delay: Base delay in seconds
            max_delay: Maximum delay in seconds
            jitter: Jitter factor (0.0-1.0)
        """
        self.retry_on = retry_on or [TimeoutError, RuntimeError]
        self.attempts = attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.jitter = jitter
    
    def should_retry(self, exception: Exception, attempt: int) -> bool:
        """
        Determine if an exception should trigger a retry.
        
        Args:
            exception: The exception that occurred
            attempt: Current attempt number (1-based)
            
        Returns:
            True if should retry, False otherwise
        """
        if attempt >= self.attempts:
            return False
        
        # Check if exception type is retryable
        if not any(isinstance(exception, exc_type) for exc_type in self.retry_on):
            return False
        
        # Check for 5xx errors in RuntimeError messages
        if isinstance(exception, RuntimeError):
            error_msg = str(exception).lower()
            if any(code in error_msg for code in ["500", "502", "503", "504"]):
                return True
            return False
        
        return True
    
    def get_delay(self, attempt: int) -> float:
        """
        Calculate delay for given attempt with exponential backoff and jitter.
        
        Args:
            attempt: Current attempt number (1-based)
            
        Returns:
            Delay in seconds
        """
        # Exponential backoff: base_delay * (2 ^ (attempt - 1))
        delay = self.base_delay * (2 ** (attempt - 1))
        
        # Cap at max_delay
        delay = min(delay, self.max_delay)
        
        # Add jitter: ±jitter% of the delay
        jitter_amount = delay * self.jitter
        delay += random.uniform(-jitter_amount, jitter_amount)
        
        # Ensure non-negative
        return max(0, delay)


class CircuitBreaker:
    """
    Circuit breaker implementation with state management.
    """
    
    def __init__(self, 
                 name: str,
                 threshold: int = 5,
                 window_s: int = 60,
                 cool_off_s: int = 60):
        """
        Initialize circuit breaker.
        
        Args:
            name: Circuit breaker name for cache keys
            threshold: Number of failures to open circuit
            window_s: Rolling window size in seconds
            cool_off_s: Cool-off period in seconds
        """
        self.name = name
        self.threshold = threshold
        self.window_s = window_s
        self.cool_off_s = cool_off_s
        self.cache_key_prefix = f"cb:{name}"
    
    def _get_state_key(self) -> str:
        """Get cache key for circuit breaker state."""
        return f"{self.cache_key_prefix}:state"
    
    def _get_failures_key(self) -> str:
        """Get cache key for failure timestamps."""
        return f"{self.cache_key_prefix}:failures"
    
    def _get_last_failure_key(self) -> str:
        """Get cache key for last failure timestamp."""
        return f"{self.cache_key_prefix}:last_failure"
    
    def get_state(self) -> CircuitBreakerState:
        """
        Get current circuit breaker state.
        
        Returns:
            Current state
        """
        state_str = cache.get(self._get_state_key(), CircuitBreakerState.CLOSED.value)
        return CircuitBreakerState(state_str)
    
    def _set_state(self, state: CircuitBreakerState):
        """Set circuit breaker state."""
        old_state = self.get_state()
        cache.set(self._get_state_key(), state.value, timeout=self.cool_off_s * 2)
        
        # Log state transition
        log_breaker_transition(self.name, old_state.value, state.value)
    
    def _record_failure(self):
        """Record a failure timestamp."""
        now = time.time()
        
        # Get existing failures
        failures = cache.get(self._get_failures_key(), [])
        
        # Add new failure
        failures.append(now)
        
        # Keep only failures within the rolling window
        cutoff = now - self.window_s
        failures = [f for f in failures if f > cutoff]
        
        # Store updated failures
        cache.set(self._get_failures_key(), failures, timeout=self.window_s * 2)
        cache.set(self._get_last_failure_key(), now, timeout=self.cool_off_s * 2)
    
    def _record_success(self):
        """Record a successful call."""
        # If we're in HALF_OPEN state, transition to CLOSED
        if self.get_state() == CircuitBreakerState.HALF_OPEN:
            self._set_state(CircuitBreakerState.CLOSED)
        
        # Clear failure history on success
        cache.delete(self._get_failures_key())
        cache.delete(self._get_last_failure_key())
    
    def can_execute(self) -> bool:
        """
        Check if circuit breaker allows execution.
        
        Returns:
            True if execution is allowed, False otherwise
        """
        current_state = self.get_state()
        
        if current_state == CircuitBreakerState.CLOSED:
            return True
        
        elif current_state == CircuitBreakerState.OPEN:
            # Check if cool-off period has passed
            last_failure = cache.get(self._get_last_failure_key())
            if last_failure and (time.time() - last_failure) >= self.cool_off_s:
                self._set_state(CircuitBreakerState.HALF_OPEN)
                return True
            return False
        
        elif current_state == CircuitBreakerState.HALF_OPEN:
            return True
        
        return False
    
    def on_success(self):
        """Handle successful execution."""
        current_state = self.get_state()
        
        if current_state == CircuitBreakerState.HALF_OPEN:
            # Success in half-open state closes the circuit
            self._set_state(CircuitBreakerState.CLOSED)
            self._record_success()
        elif current_state == CircuitBreakerState.CLOSED:
            # Record success to maintain healthy state
            self._record_success()
    
    def on_failure(self):
        """Handle failed execution."""
        current_state = self.get_state()
        
        if current_state == CircuitBreakerState.HALF_OPEN:
            # Failure in half-open state opens the circuit
            self._set_state(CircuitBreakerState.OPEN)
            self._record_failure()
        
        elif current_state == CircuitBreakerState.CLOSED:
            # Record failure and check threshold
            self._record_failure()
            
            # Check if threshold is reached
            failures = cache.get(self._get_failures_key(), [])
            if len(failures) >= self.threshold:
                self._set_state(CircuitBreakerState.OPEN)
                self._record_failure()
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get circuit breaker metrics.
        
        Returns:
            Dict with current state and failure count
        """
        failures = cache.get(self._get_failures_key(), [])
        return {
            "state": self.get_state().value,
            "failure_count": len(failures),
            "threshold": self.threshold,
            "window_s": self.window_s,
            "cool_off_s": self.cool_off_s
        }
