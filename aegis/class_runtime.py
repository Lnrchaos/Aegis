"""
Class and OOP runtime support for Aegis
Provides class instantiation, method dispatch, and inheritance.
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass
from .runtime import Environment, RuntimeErrorAegis, FunctionValue


@dataclass
class ClassInstance:
    """Represents an instance of a class."""
    class_name: str
    fields: Dict[str, Any]
    methods: Dict[str, FunctionValue]
    superclass: Optional['ClassInstance'] = None
    
    def get_field(self, name: str) -> Any:
        """Get a field value."""
        if name in self.fields:
            return self.fields[name]
        if self.superclass:
            return self.superclass.get_field(name)
        raise RuntimeErrorAegis(f"Field '{name}' not found in {self.class_name}")
    
    def set_field(self, name: str, value: Any) -> None:
        """Set a field value."""
        self.fields[name] = value
    
    def get_method(self, name: str) -> Optional[FunctionValue]:
        """Get a method by name."""
        if name in self.methods:
            return self.methods[name]
        if self.superclass:
            return self.superclass.get_method(name)
        return None
    
    def call_method(self, name: str, args: List[Any], env: Environment) -> Any:
        """Call a method on this instance."""
        method = self.get_method(name)
        if method is None:
            raise RuntimeErrorAegis(f"Method '{name}' not found in {self.class_name}")
        
        # Create new environment with 'this' bound to self
        method_env = Environment(outer=method.env)
        method_env.define("this", self)
        
        # Bind arguments
        for i, param in enumerate(method.params):
            if i < len(args):
                method_env.define(param, args[i])
            else:
                method_env.define(param, None)
        
        # Execute method body
        from .interpreter import evaluate
        return evaluate(method.body, method_env)


@dataclass
class ClassDefinition:
    """Represents a class definition."""
    name: str
    superclass: Optional[str]
    methods: Dict[str, FunctionValue]
    static_methods: Dict[str, FunctionValue]
    
    def instantiate(self, args: List[Any], env: Environment) -> ClassInstance:
        """Create a new instance of this class."""
        instance = ClassInstance(
            class_name=self.name,
            fields={},
            methods=self.methods.copy()
        )
        
        # Call constructor if it exists
        constructor = self.methods.get("__init__")
        if constructor:
            # Create environment for constructor
            constructor_env = Environment(outer=constructor.env)
            constructor_env.define("this", instance)
            
            # Bind arguments
            for i, param in enumerate(constructor.params):
                if i < len(args):
                    constructor_env.define(param, args[i])
                else:
                    constructor_env.define(param, None)
            
            # Execute constructor
            from .interpreter import evaluate
            evaluate(constructor.body, constructor_env)
        
        return instance


class ClassRuntime:
    """Manages class definitions and instantiation."""
    
    def __init__(self):
        self.classes: Dict[str, ClassDefinition] = {}
    
    def define_class(self, name: str, superclass: Optional[str], 
                    methods: Dict[str, FunctionValue], 
                    static_methods: Dict[str, FunctionValue]) -> None:
        """Define a new class."""
        if superclass and superclass not in self.classes:
            raise RuntimeErrorAegis(f"Superclass '{superclass}' not found")
        
        self.classes[name] = ClassDefinition(
            name=name,
            superclass=superclass,
            methods=methods,
            static_methods=static_methods
        )
    
    def get_class(self, name: str) -> Optional[ClassDefinition]:
        """Get a class definition by name."""
        return self.classes.get(name)
    
    def instantiate_class(self, name: str, args: List[Any], env: Environment) -> ClassInstance:
        """Instantiate a class by name."""
        class_def = self.get_class(name)
        if class_def is None:
            raise RuntimeErrorAegis(f"Class '{name}' not found")
        
        return class_def.instantiate(args, env)
    
    def call_static_method(self, class_name: str, method_name: str, 
                          args: List[Any], env: Environment) -> Any:
        """Call a static method on a class."""
        class_def = self.get_class(class_name)
        if class_def is None:
            raise RuntimeErrorAegis(f"Class '{class_name}' not found")
        
        method = class_def.static_methods.get(method_name)
        if method is None:
            raise RuntimeErrorAegis(f"Static method '{method_name}' not found in {class_name}")
        
        # Create environment for static method
        method_env = Environment(outer=method.env)
        
        # Bind arguments
        for i, param in enumerate(method.params):
            if i < len(args):
                method_env.define(param, args[i])
            else:
                method_env.define(param, None)
        
        # Execute method
        from .interpreter import evaluate
        return evaluate(method.body, method_env)


# Global class runtime instance
_class_runtime = ClassRuntime()


def get_class_runtime() -> ClassRuntime:
    """Get the global class runtime instance."""
    return _class_runtime


def make_class_functions() -> Dict[str, Any]:
    """Create class-related native functions for the environment."""
    
    def new_instance(args: List[Any]) -> Any:
        """Native function to create a new class instance."""
        if not args:
            raise RuntimeErrorAegis("new requires a class name")
        
        class_name = args[0]
        constructor_args = args[1:] if len(args) > 1 else []
        
        return _class_runtime.instantiate_class(class_name, constructor_args, None)
    
    def get_super(args: List[Any]) -> Any:
        """Native function to get superclass reference."""
        if not args:
            raise RuntimeErrorAegis("super requires a method name")
        
        method_name = args[0]
        method_args = args[1:] if len(args) > 1 else []
        
        # This would need access to the current 'this' context
        # For now, return a placeholder
        return f"super.{method_name}({', '.join(map(str, method_args))})"
    
    def is_instance(args: List[Any]) -> Any:
        """Native function to check if an object is an instance of a class."""
        if len(args) < 2:
            raise RuntimeErrorAegis("is_instance requires object and class name")
        
        obj = args[0]
        class_name = args[1]
        
        if isinstance(obj, ClassInstance):
            return obj.class_name == class_name
        return False
    
    return {
        "new": new_instance,
        "super": get_super,
        "is_instance": is_instance,
    }
