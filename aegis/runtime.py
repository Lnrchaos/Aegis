from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, Optional, List, Callable, Tuple
import json


class RuntimeErrorAegis(Exception):
    pass


# Simple stack frames for tracing
_eval_stack: List[str] = []


def enter_frame(name: str) -> None:
    _eval_stack.append(name)


def exit_frame() -> None:
    if _eval_stack:
        _eval_stack.pop()


def current_stack() -> List[str]:
    return list(_eval_stack)


class ReturnSignal(Exception):
    def __init__(self, value: Any):
        self.value = value


class Environment:
    def __init__(self, outer: Optional['Environment'] = None):
        self.store: Dict[str, Any] = {}
        self.outer = outer

    def define(self, name: str, value: Any) -> None:
        self.store[name] = value

    def get(self, name: str) -> Any:
        if name in self.store:
            return self.store[name]
        if self.outer is not None:
            return self.outer.get(name)
        raise RuntimeErrorAegis(f"Undefined identifier '{name}'")

    def assign(self, name: str, value: Any) -> None:
        if name in self.store:
            self.store[name] = value
            return
        if self.outer is not None:
            # Try to assign in outer scopes; if not found at any level, we'll define in current scope
            try:
                self.outer.assign(name, value)
                return
            except RuntimeErrorAegis:
                # fall through to define in current scope
                pass
        # declare-if-undefined semantics for 'set'
        self.define(name, value)


@dataclass
class FunctionValue:
    name: Optional[str]
    params: List[str]
    body: Any  # Block
    env: Environment


@dataclass
class NativeFunction:
    name: str
    func: Callable[[List[Any]], Any]

    def __call__(self, args: List[Any]) -> Any:
        enter_frame(self.name)
        try:
            return self.func(args)
        finally:
            exit_frame()



def is_truthy(value: Any) -> bool:
    if value is None:
        return False
    if value is False:
        return False
    return True


def deep_equal(a: Any, b: Any) -> bool:
    try:
        return json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)
    except Exception:
        return a == b


