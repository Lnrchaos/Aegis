from __future__ import annotations
from typing import List
from pathlib import Path

from .parser import parse, ParseError
from .runtime import Environment, RuntimeErrorAegis, current_stack
from .interpreter import evaluate
from .env import make_global_env


def run_file(path: str, argv: List[str]) -> int:
    p = Path(path)
    if not p.exists():
        print(f"File not found: {path}")
        return 1
    try:
        source = p.read_text(encoding="utf-8")
        program = parse(source)
        env = make_global_env()
        env.define("ARGV", argv)
        result = evaluate(program, env)
        if result is not None:
            print(result)
        return 0
    except ParseError as pe:
        print(f"Parse error: {pe}")
        return 2
    except RuntimeErrorAegis as re:
        print(f"Runtime error: {re}")
        st = current_stack()
        if st:
            print("Stack:")
            for f in reversed(st):
                print(f"  at {f}()")
        return 3


