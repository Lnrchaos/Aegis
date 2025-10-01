"""
Error handling and exception management for Aegis
Provides try/catch/finally, assertions, and error types.
"""

from __future__ import annotations
from typing import Any, Optional, List, Dict
from dataclasses import dataclass
from .runtime import RuntimeErrorAegis


@dataclass
class AegisError:
    """Base error type for Aegis exceptions."""
    message: str
    line: int = 0
    col: int = 0
    stack_trace: List[str] = None
    
    def __post_init__(self):
        if self.stack_trace is None:
            self.stack_trace = []


@dataclass
class TypeError(AegisError):
    """Type error for invalid type operations."""
    expected_type: str = ""
    actual_type: str = ""


@dataclass
class ValueError(AegisError):
    """Value error for invalid values."""
    pass


@dataclass
class ReferenceError(AegisError):
    """Reference error for undefined variables."""
    variable_name: str = ""


@dataclass
class SyntaxError(AegisError):
    """Syntax error for invalid syntax."""
    pass


@dataclass
class RuntimeError(AegisError):
    """Runtime error for execution failures."""
    pass


class ErrorHandler:
    """Manages error handling and exception propagation."""
    
    def __init__(self):
        self.current_exception: Optional[AegisError] = None
        self.stack_trace: List[str] = []
    
    def throw(self, error: AegisError) -> None:
        """Throw an error, setting it as the current exception."""
        self.current_exception = error
        self.add_to_stack_trace(f"at line {error.line}:{error.col}")
        raise RuntimeErrorAegis(error.message)
    
    def catch(self, error_type: Optional[str] = None) -> bool:
        """Check if current exception matches the error type."""
        if self.current_exception is None:
            return False
        
        if error_type is None:
            return True
        
        # Simple type matching
        return error_type.lower() in str(type(self.current_exception)).lower()
    
    def get_exception(self) -> Optional[AegisError]:
        """Get the current exception."""
        return self.current_exception
    
    def clear_exception(self) -> None:
        """Clear the current exception."""
        self.current_exception = None
    
    def add_to_stack_trace(self, frame: str) -> None:
        """Add a frame to the stack trace."""
        self.stack_trace.append(frame)
    
    def get_stack_trace(self) -> List[str]:
        """Get the current stack trace."""
        return self.stack_trace.copy()


# Global error handler instance
_error_handler = ErrorHandler()


def get_error_handler() -> ErrorHandler:
    """Get the global error handler instance."""
    return _error_handler


def make_error_functions() -> Dict[str, Any]:
    """Create error-related native functions for the environment."""
    from .runtime import NativeFunction
    
    def throw_error(args: List[Any]) -> Any:
        """Native function to throw an error."""
        if not args:
            raise RuntimeErrorAegis("throw requires an error message")
        
        message = str(args[0])
        error = RuntimeError(message, line=0, col=0)
        _error_handler.throw(error)
        return None
    
    def assert_condition(args: List[Any]) -> Any:
        """Native function for assertions."""
        if not args:
            raise RuntimeErrorAegis("assert requires a condition")
        
        condition = args[0]
        message = str(args[1]) if len(args) > 1 else "Assertion failed"
        
        if not condition:
            error = RuntimeError(message, line=0, col=0)
            _error_handler.throw(error)
        
        return True
    
    def create_error(args: List[Any]) -> Any:
        """Native function to create error objects."""
        if not args:
            return RuntimeError("Unknown error")
        
        error_type = args[0].lower()
        message = str(args[1]) if len(args) > 1 else "Error"
        
        if error_type == "type":
            return TypeError(message)
        elif error_type == "value":
            return ValueError(message)
        elif error_type == "reference":
            return ReferenceError(message)
        elif error_type == "syntax":
            return SyntaxError(message)
        else:
            return RuntimeError(message)
    
    def get_exception_info(args: List[Any]) -> Any:
        """Native function to get current exception information."""
        exception = _error_handler.get_exception()
        if exception is None:
            return None
        
        return {
            "message": exception.message,
            "line": exception.line,
            "col": exception.col,
            "type": type(exception).__name__,
            "stack_trace": exception.stack_trace
        }
    
    return {
        "throw": NativeFunction("throw", throw_error),
        "assert": NativeFunction("assert", assert_condition),
        "create_error": NativeFunction("create_error", create_error),
        "get_exception": NativeFunction("get_exception", get_exception_info),
    }
