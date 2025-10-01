import types
import pytest

from aegis.parser import parse
from aegis.interpreter import evaluate
from aegis.env import make_global_env


def run(src: str):
    env = make_global_env()
    program = parse(src)
    return evaluate(program, env)


def test_arithmetic_string_array():
    assert run("1 + 2;") == 3
    assert run('"a" + 1;') == "a1"
    assert run('[1,2] + [3];') == [1,2,3]


def test_let_set_and_if_while():
    src = """
    let x = 1;
    set x = x + 2;
    let i = 0;
    while (i < 3) { set i = i + 1; }
    x + i;
    """
    assert run(src) == 6


def test_function_call_and_return():
    src = """
    fn add(a,b) { return a + b; }
    let r = add(2, 3);
    r;
    """
    assert run(src) == 5


def test_regex():
    src = """
    let m = regex.search("h(.*)o", "hello");
    m.groups[0];
    """
    assert run(src) == "ell"
