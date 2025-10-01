from __future__ import annotations
from pathlib import Path
from typing import Dict, Any

from .parser import parse
from .interpreter import evaluate


class ModuleCache:
    def __init__(self):
        self.cache: Dict[str, Any] = {}

    def has(self, key: str) -> bool:
        return key in self.cache

    def get(self, key: str) -> Any:
        return self.cache.get(key)

    def set(self, key: str, value: Any) -> None:
        self.cache[key] = value


_module_cache = ModuleCache()


def require(path_like: str) -> Any:
    # Lazy import to avoid circular dependency with env
    from .env import make_global_env  # type: ignore

    p = Path(path_like)
    if p.suffix == "":
        p = p.with_suffix(".aeg")
    full = str(p.resolve())
    if _module_cache.has(full):
        return _module_cache.get(full)
    source = p.read_text(encoding="utf-8")
    program = parse(source)
    env = make_global_env()
    result = evaluate(program, env)
    _module_cache.set(full, result)
    return result


def load_file(path_like: str) -> Any:
    return require(path_like)
