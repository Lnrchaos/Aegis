from __future__ import annotations
from .runtime import Environment
from .builtins import make_http, make_html, make_crypto, make_encoding, make_url, make_regex, make_fs, make_time
from .security import SECURITY_FUNCTIONS
from .modules import require as _require, load_file as _load_file
from .runtime import NativeFunction


def _wrap(fn):
    def inner(args):
        return fn(*args)
    return NativeFunction(name=fn.__name__, func=inner)


def make_global_env() -> Environment:
    env = Environment()
    # sandbox flags
    sandbox = {"fs": False}
    env.define("sandbox", sandbox)

    env.define("http", make_http())
    env.define("html", make_html())
    env.define("crypto", make_crypto())
    env.define("encoding", make_encoding())
    env.define("url", make_url())
    env.define("regex", make_regex())
    env.define("time", make_time())
    env.define("fs", make_fs(sandbox))

    env.define("module", {
        "require": _wrap(_require),
        "load_file": _wrap(_load_file),
    })
    
    # Add security functions
    for name, func in SECURITY_FUNCTIONS.items():
        env.define(name, func)
    
    # Add print function
    def print_func(args):
        print(*[str(arg) for arg in args])
        return None
    env.define("print", NativeFunction("print", print_func))
    
    return env
