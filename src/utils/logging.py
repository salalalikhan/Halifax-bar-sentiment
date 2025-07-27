"""Advanced logging configuration with structured logging and monitoring."""

import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
import traceback

# Optional advanced logging dependencies
try:
    from loguru import logger as loguru_logger
    LOGURU_AVAILABLE = True
except ImportError:
    loguru_logger = None
    LOGURU_AVAILABLE = False

try:
    import structlog
    STRUCTLOG_AVAILABLE = True
except ImportError:
    structlog = None
    STRUCTLOG_AVAILABLE = False


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "thread": record.thread,
            "process": record.process,
        }
        
        # Add extra fields if present
        if hasattr(record, 'extra_data'):
            log_data.update(record.extra_data)
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": traceback.format_exception(*record.exc_info)
            }
        
        return json.dumps(log_data, default=str)


class StructuredLogger:
    """Structured logger with context and metrics."""
    
    def __init__(self, name: str, log_level: str = "INFO"):
        self.name = name
        self.log_level = log_level
        self.context: Dict[str, Any] = {}
        self._setup_logger()
    
    def _setup_logger(self):
        """Set up structured logging."""
        if STRUCTLOG_AVAILABLE:
            # Configure structlog
            structlog.configure(
                processors=[
                    structlog.stdlib.filter_by_level,
                    structlog.stdlib.add_logger_name,
                    structlog.stdlib.add_log_level,
                    structlog.stdlib.PositionalArgumentsFormatter(),
                    structlog.processors.TimeStamper(fmt="iso"),
                    structlog.processors.StackInfoRenderer(),
                    structlog.processors.format_exc_info,
                    structlog.processors.UnicodeDecoder(),
                    structlog.processors.JSONRenderer()
                ],
                context_class=dict,
                logger_factory=structlog.stdlib.LoggerFactory(),
                wrapper_class=structlog.stdlib.BoundLogger,
                cache_logger_on_first_use=True,
            )
            
            # Get structured logger
            self.logger = structlog.get_logger(self.name)
        else:
            # Fallback to standard logging
            self.logger = logging.getLogger(self.name)
            self.logger.setLevel(getattr(logging, self.log_level.upper()))
    
    def add_context(self, **kwargs):
        """Add context to all subsequent log messages."""
        self.context.update(kwargs)
        if STRUCTLOG_AVAILABLE:
            self.logger = self.logger.bind(**self.context)
    
    def clear_context(self):
        """Clear logging context."""
        self.context.clear()
        if STRUCTLOG_AVAILABLE:
            self.logger = structlog.get_logger(self.name)
    
    def _log_with_context(self, level: str, message: str, **kwargs):
        """Log message with context."""
        if STRUCTLOG_AVAILABLE:
            getattr(self.logger, level.lower())(message, **kwargs)
        else:
            # Format context for standard logging
            context_str = " ".join(f"{k}={v}" for k, v in {**self.context, **kwargs}.items())
            full_message = f"{message} {context_str}" if context_str else message
            getattr(self.logger, level.lower())(full_message)
    
    def info(self, message: str, **kwargs):
        """Log info message with context."""
        self._log_with_context("info", message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning message with context."""
        self._log_with_context("warning", message, **kwargs)
    
    def error(self, message: str, **kwargs):
        """Log error message with context."""
        self._log_with_context("error", message, **kwargs)
    
    def debug(self, message: str, **kwargs):
        """Log debug message with context."""
        self._log_with_context("debug", message, **kwargs)
    
    def critical(self, message: str, **kwargs):
        """Log critical message with context."""
        self._log_with_context("critical", message, **kwargs)


class PerformanceMonitor:
    """Performance monitoring and metrics collection."""
    
    def __init__(self, logger: StructuredLogger):
        self.logger = logger
        self.metrics: Dict[str, Any] = {}
    
    def start_timer(self, operation: str):
        """Start timing an operation."""
        self.metrics[f"{operation}_start"] = datetime.now()
        self.logger.debug(f"Started operation: {operation}")
    
    def end_timer(self, operation: str, **context):
        """End timing an operation and log metrics."""
        start_key = f"{operation}_start"
        if start_key in self.metrics:
            start_time = self.metrics[start_key]
            duration = (datetime.now() - start_time).total_seconds()
            
            self.logger.info(
                f"Operation completed: {operation}",
                duration_seconds=duration,
                operation=operation,
                **context
            )
            
            # Clean up
            del self.metrics[start_key]
            
            return duration
        else:
            self.logger.warning(f"No start time found for operation: {operation}")
            return None
    
    def record_metric(self, metric_name: str, value: Any, **context):
        """Record a custom metric."""
        self.logger.info(
            f"Metric recorded: {metric_name}",
            metric_name=metric_name,
            metric_value=value,
            **context
        )
    
    def record_counter(self, counter_name: str, increment: int = 1, **context):
        """Record a counter metric."""
        if counter_name not in self.metrics:
            self.metrics[counter_name] = 0
        
        self.metrics[counter_name] += increment
        
        self.logger.info(
            f"Counter updated: {counter_name}",
            counter_name=counter_name,
            counter_value=self.metrics[counter_name],
            increment=increment,
            **context
        )
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get all recorded metrics."""
        return self.metrics.copy()


class HealthChecker:
    """System health monitoring."""
    
    def __init__(self, logger: StructuredLogger):
        self.logger = logger
        self.health_checks: Dict[str, callable] = {}
    
    def register_check(self, name: str, check_func: callable):
        """Register a health check function."""
        self.health_checks[name] = check_func
        self.logger.info(f"Health check registered: {name}")
    
    def run_checks(self) -> Dict[str, Any]:
        """Run all health checks."""
        results = {}
        overall_healthy = True
        
        for name, check_func in self.health_checks.items():
            try:
                result = check_func()
                results[name] = {
                    "status": "healthy" if result else "unhealthy",
                    "details": result if isinstance(result, dict) else {}
                }
                
                if not result:
                    overall_healthy = False
                    
            except Exception as e:
                results[name] = {
                    "status": "error",
                    "details": {"error": str(e), "type": type(e).__name__}
                }
                overall_healthy = False
                
                self.logger.error(
                    f"Health check failed: {name}",
                    check_name=name,
                    error=str(e),
                    exc_info=True
                )
        
        overall_status = {
            "overall_status": "healthy" if overall_healthy else "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "checks": results
        }
        
        self.logger.info(
            "Health check completed",
            overall_status=overall_status["overall_status"],
            check_count=len(self.health_checks),
            healthy_count=sum(1 for r in results.values() if r["status"] == "healthy")
        )
        
        return overall_status


class ErrorTracker:
    """Error tracking and alerting."""
    
    def __init__(self, logger: StructuredLogger):
        self.logger = logger
        self.error_counts: Dict[str, int] = {}
        self.error_threshold = 10  # Alert after 10 errors of same type
    
    def track_error(self, error: Exception, context: Dict[str, Any] = None):
        """Track an error and check for alerting."""
        error_type = type(error).__name__
        error_message = str(error)
        
        # Update error count
        if error_type not in self.error_counts:
            self.error_counts[error_type] = 0
        self.error_counts[error_type] += 1
        
        # Log error with context
        self.logger.error(
            f"Error tracked: {error_type}",
            error_type=error_type,
            error_message=error_message,
            error_count=self.error_counts[error_type],
            context=context or {},
            exc_info=True
        )
        
        # Check for alerting threshold
        if self.error_counts[error_type] >= self.error_threshold:
            self._trigger_alert(error_type, self.error_counts[error_type])
    
    def _trigger_alert(self, error_type: str, count: int):
        """Trigger an alert for repeated errors."""
        self.logger.critical(
            f"ERROR THRESHOLD EXCEEDED: {error_type}",
            error_type=error_type,
            error_count=count,
            threshold=self.error_threshold,
            alert_triggered=True
        )
    
    def get_error_summary(self) -> Dict[str, Any]:
        """Get summary of tracked errors."""
        return {
            "total_errors": sum(self.error_counts.values()),
            "error_types": len(self.error_counts),
            "error_counts": self.error_counts.copy(),
            "timestamp": datetime.now().isoformat()
        }


class LoggingConfig:
    """Central logging configuration."""
    
    @staticmethod
    def setup_logging(
        log_level: str = "INFO",
        log_file: Optional[str] = None,
        enable_json: bool = True,
        enable_console: bool = True
    ):
        """Set up application logging."""
        # Remove default handlers
        for handler in logging.root.handlers[:]:
            logging.root.removeHandler(handler)
        
        # Create formatters
        if enable_json:
            json_formatter = JSONFormatter()
        else:
            console_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
        
        # Console handler
        if enable_console:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(json_formatter if enable_json else console_formatter)
            logging.root.addHandler(console_handler)
        
        # File handler
        if log_file:
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(json_formatter if enable_json else console_formatter)
            logging.root.addHandler(file_handler)
        
        # Set level
        logging.root.setLevel(getattr(logging, log_level.upper()))
        
        # Configure loguru for additional features if available
        if LOGURU_AVAILABLE:
            loguru_logger.remove()  # Remove default handler
            
            if enable_console:
                loguru_logger.add(
                    sys.stdout,
                    level=log_level,
                    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}",
                    serialize=enable_json
                )
            
            if log_file:
                loguru_logger.add(
                    log_file.replace('.log', '_loguru.log'),
                    level=log_level,
                    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}",
                    serialize=enable_json,
                    rotation="1 day",
                    retention="30 days",
                    compression="gzip"
                )
            
            return loguru_logger
        else:
            # Return standard logger if loguru not available
            return logging.getLogger("app")


# Global logger instances
main_logger = StructuredLogger("halifax_bar_sentiment")
performance_monitor = PerformanceMonitor(main_logger)
health_checker = HealthChecker(main_logger)
error_tracker = ErrorTracker(main_logger)


# Context managers for common logging patterns
class LoggedOperation:
    """Context manager for logging operations with timing."""
    
    def __init__(self, operation_name: str, logger: StructuredLogger = None, **context):
        self.operation_name = operation_name
        self.logger = logger or main_logger
        self.context = context
        self.monitor = PerformanceMonitor(self.logger)
    
    def __enter__(self):
        self.monitor.start_timer(self.operation_name)
        self.logger.info(f"Starting operation: {self.operation_name}", **self.context)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.logger.error(
                f"Operation failed: {self.operation_name}",
                error_type=exc_type.__name__,
                error_message=str(exc_val),
                **self.context
            )
            error_tracker.track_error(exc_val, self.context)
        else:
            duration = self.monitor.end_timer(self.operation_name, **self.context)
            self.logger.info(
                f"Operation completed: {self.operation_name}",
                duration_seconds=duration,
                **self.context
            )


def setup_application_logging():
    """Set up logging for the entire application."""
    # Create logs directory
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Setup main logging
    LoggingConfig.setup_logging(
        log_level="INFO",
        log_file=str(log_dir / "halifax_bar_sentiment.log"),
        enable_json=True,
        enable_console=True
    )
    
    # Register default health checks
    def check_disk_space():
        """Check available disk space."""
        import shutil
        total, used, free = shutil.disk_usage(".")
        free_percent = (free / total) * 100
        return free_percent > 10  # Alert if less than 10% free
    
    def check_memory_usage():
        """Check memory usage."""
        try:
            import psutil
            memory = psutil.virtual_memory()
            return memory.percent < 90  # Alert if more than 90% used
        except ImportError:
            return True  # Skip check if psutil not available
    
    health_checker.register_check("disk_space", check_disk_space)
    health_checker.register_check("memory_usage", check_memory_usage)
    
    main_logger.info("Application logging configured")
    
    return main_logger


# Convenience functions for backward compatibility
def get_logger(name: str = "halifax_bar_sentiment") -> logging.Logger:
    """Get a standard Python logger."""
    return logging.getLogger(name)


def setup_logging(log_level: str = "INFO"):
    """Simple logging setup function."""
    return setup_application_logging()