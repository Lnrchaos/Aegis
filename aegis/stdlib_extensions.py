"""
Extended standard library modules for Aegis
Provides additional built-in modules for common operations.
"""

from __future__ import annotations
import os
import sys
import json
import csv
import yaml
import toml
import uuid
import random
import string
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
import re
from .runtime import NativeFunction


def make_filesystem() -> Dict[str, Any]:
    """Enhanced filesystem operations."""
    
    def read_file(args: List[Any]) -> Any:
        if not args:
            raise ValueError("read_file requires a path")
        path = Path(args[0])
        encoding = args[1] if len(args) > 1 else "utf-8"
        return path.read_text(encoding=encoding)
    
    def write_file(args: List[Any]) -> Any:
        if len(args) < 2:
            raise ValueError("write_file requires path and content")
        path = Path(args[0])
        content = args[1]
        encoding = args[2] if len(args) > 2 else "utf-8"
        path.write_text(content, encoding=encoding)
        return True
    
    def list_dir(args: List[Any]) -> Any:
        if not args:
            raise ValueError("list_dir requires a path")
        path = Path(args[0])
        recursive = args[1] if len(args) > 1 else False
        if recursive:
            return [str(p) for p in path.rglob("*") if p.is_file()]
        return [str(p) for p in path.iterdir()]
    
    def exists(args: List[Any]) -> Any:
        if not args:
            raise ValueError("exists requires a path")
        return Path(args[0]).exists()
    
    def is_file(args: List[Any]) -> Any:
        if not args:
            raise ValueError("is_file requires a path")
        return Path(args[0]).is_file()
    
    def is_dir(args: List[Any]) -> Any:
        if not args:
            raise ValueError("is_dir requires a path")
        return Path(args[0]).is_dir()
    
    def mkdir(args: List[Any]) -> Any:
        if not args:
            raise ValueError("mkdir requires a path")
        path = Path(args[0])
        parents = args[1] if len(args) > 1 else False
        path.mkdir(parents=parents, exist_ok=True)
        return True
    
    def remove(args: List[Any]) -> Any:
        if not args:
            raise ValueError("remove requires a path")
        path = Path(args[0])
        if path.is_file():
            path.unlink()
        elif path.is_dir():
            import shutil
            shutil.rmtree(path)
        return True
    
    return {
        "read_file": NativeFunction("read_file", read_file),
        "write_file": NativeFunction("write_file", write_file),
        "list_dir": NativeFunction("list_dir", list_dir),
        "exists": NativeFunction("exists", exists),
        "is_file": NativeFunction("is_file", is_file),
        "is_dir": NativeFunction("is_dir", is_dir),
        "mkdir": NativeFunction("mkdir", mkdir),
        "remove": NativeFunction("remove", remove),
    }


def make_json() -> Dict[str, Any]:
    """JSON serialization and parsing."""
    
    def parse(args: List[Any]) -> Any:
        if not args:
            raise ValueError("json.parse requires a string")
        return json.loads(args[0])
    
    def stringify(args: List[Any]) -> Any:
        if not args:
            raise ValueError("json.stringify requires a value")
        indent = args[1] if len(args) > 1 else None
        return json.dumps(args[0], indent=indent)
    
    def read_file(args: List[Any]) -> Any:
        if not args:
            raise ValueError("json.read_file requires a path")
        path = Path(args[0])
        return json.loads(path.read_text())
    
    def write_file(args: List[Any]) -> Any:
        if len(args) < 2:
            raise ValueError("json.write_file requires path and data")
        path = Path(args[0])
        data = args[1]
        indent = args[2] if len(args) > 2 else 2
        path.write_text(json.dumps(data, indent=indent))
        return True
    
    return {
        "parse": NativeFunction("parse", parse),
        "stringify": NativeFunction("stringify", stringify),
        "read_file": NativeFunction("read_file", read_file),
        "write_file": NativeFunction("write_file", write_file),
    }


def make_yaml() -> Dict[str, Any]:
    """YAML serialization and parsing."""
    
    def parse(args: List[Any]) -> Any:
        if not args:
            raise ValueError("yaml.parse requires a string")
        return yaml.safe_load(args[0])
    
    def dump(args: List[Any]) -> Any:
        if not args:
            raise ValueError("yaml.dump requires a value")
        return yaml.dump(args[0])
    
    def read_file(args: List[Any]) -> Any:
        if not args:
            raise ValueError("yaml.read_file requires a path")
        path = Path(args[0])
        return yaml.safe_load(path.read_text())
    
    def write_file(args: List[Any]) -> Any:
        if len(args) < 2:
            raise ValueError("yaml.write_file requires path and data")
        path = Path(args[0])
        data = args[1]
        path.write_text(yaml.dump(data))
        return True
    
    return {
        "parse": NativeFunction("parse", parse),
        "dump": NativeFunction("dump", dump),
        "read_file": NativeFunction("read_file", read_file),
        "write_file": NativeFunction("write_file", write_file),
    }


def make_random() -> Dict[str, Any]:
    """Random number and string generation."""
    
    def random_int(args: List[Any]) -> Any:
        if len(args) < 2:
            raise ValueError("random_int requires min and max")
        return random.randint(args[0], args[1])
    
    def random_float(args: List[Any]) -> Any:
        if len(args) < 2:
            raise ValueError("random_float requires min and max")
        return random.uniform(args[0], args[1])
    
    def random_choice(args: List[Any]) -> Any:
        if not args:
            raise ValueError("random_choice requires a list")
        return random.choice(args[0])
    
    def random_string(args: List[Any]) -> Any:
        length = args[0] if args else 10
        chars = args[1] if len(args) > 1 else string.ascii_letters + string.digits
        return ''.join(random.choice(chars) for _ in range(length))
    
    def uuid4(args: List[Any]) -> Any:
        return str(uuid.uuid4())
    
    def shuffle(args: List[Any]) -> Any:
        if not args:
            raise ValueError("shuffle requires a list")
        lst = args[0].copy()
        random.shuffle(lst)
        return lst
    
    return {
        "int": NativeFunction("int", random_int),
        "float": NativeFunction("float", random_float),
        "choice": NativeFunction("choice", random_choice),
        "string": NativeFunction("string", random_string),
        "uuid": NativeFunction("uuid", uuid4),
        "shuffle": NativeFunction("shuffle", shuffle),
    }


def make_date() -> Dict[str, Any]:
    """Date and time operations."""
    
    def now(args: List[Any]) -> Any:
        return datetime.now().isoformat()
    
    def parse(args: List[Any]) -> Any:
        if not args:
            raise ValueError("date.parse requires a string")
        return datetime.fromisoformat(args[0]).isoformat()
    
    def format(args: List[Any]) -> Any:
        if len(args) < 2:
            raise ValueError("date.format requires date and format string")
        dt = datetime.fromisoformat(args[0])
        return dt.strftime(args[1])
    
    def add_days(args: List[Any]) -> Any:
        if len(args) < 2:
            raise ValueError("add_days requires date and days")
        dt = datetime.fromisoformat(args[0])
        days = args[1]
        return (dt + timedelta(days=days)).isoformat()
    
    def diff(args: List[Any]) -> Any:
        if len(args) < 2:
            raise ValueError("diff requires two dates")
        dt1 = datetime.fromisoformat(args[0])
        dt2 = datetime.fromisoformat(args[1])
        return (dt2 - dt1).total_seconds()
    
    return {
        "now": NativeFunction("now", now),
        "parse": NativeFunction("parse", parse),
        "format": NativeFunction("format", format),
        "add_days": NativeFunction("add_days", add_days),
        "diff": NativeFunction("diff", diff),
    }


def make_process() -> Dict[str, Any]:
    """Process and system operations."""
    
    def exec(args: List[Any]) -> Any:
        if not args:
            raise ValueError("exec requires a command")
        import subprocess
        result = subprocess.run(args, capture_output=True, text=True)
        return {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode
        }
    
    def env(args: List[Any]) -> Any:
        if not args:
            return dict(os.environ)
        return os.environ.get(args[0])
    
    def cwd(args: List[Any]) -> Any:
        return str(Path.cwd())
    
    def chdir(args: List[Any]) -> Any:
        if not args:
            raise ValueError("chdir requires a path")
        os.chdir(args[0])
        return True
    
    def exit(args: List[Any]) -> Any:
        code = args[0] if args else 0
        sys.exit(code)
    
    return {
        "exec": NativeFunction("exec", exec),
        "env": NativeFunction("env", env),
        "cwd": NativeFunction("cwd", cwd),
        "chdir": NativeFunction("chdir", chdir),
        "exit": NativeFunction("exit", exit),
    }


def make_math() -> Dict[str, Any]:
    """Mathematical operations."""
    import math
    
    def sin(args: List[Any]) -> Any:
        if not args:
            raise ValueError("sin requires a number")
        return math.sin(args[0])
    
    def cos(args: List[Any]) -> Any:
        if not args:
            raise ValueError("cos requires a number")
        return math.cos(args[0])
    
    def tan(args: List[Any]) -> Any:
        if not args:
            raise ValueError("tan requires a number")
        return math.tan(args[0])
    
    def sqrt(args: List[Any]) -> Any:
        if not args:
            raise ValueError("sqrt requires a number")
        return math.sqrt(args[0])
    
    def pow(args: List[Any]) -> Any:
        if len(args) < 2:
            raise ValueError("pow requires base and exponent")
        return math.pow(args[0], args[1])
    
    def log(args: List[Any]) -> Any:
        if not args:
            raise ValueError("log requires a number")
        return math.log(args[0])
    
    def pi(args: List[Any]) -> Any:
        return math.pi
    
    def e(args: List[Any]) -> Any:
        return math.e
    
    return {
        "sin": NativeFunction("sin", sin),
        "cos": NativeFunction("cos", cos),
        "tan": NativeFunction("tan", tan),
        "sqrt": NativeFunction("sqrt", sqrt),
        "pow": NativeFunction("pow", pow),
        "log": NativeFunction("log", log),
        "pi": NativeFunction("pi", pi),
        "e": NativeFunction("e", e),
    }
