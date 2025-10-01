from __future__ import annotations
from typing import Any, List
from . import ast_nodes as AST
from .runtime import Environment, FunctionValue, NativeFunction, ReturnSignal, RuntimeErrorAegis, is_truthy, deep_equal, enter_frame, exit_frame


def evaluate(node: AST.Node, env: Environment) -> Any:
    t = type(node)
    if t is AST.Program:
        result = None
        for stmt in node.body:
            result = evaluate(stmt, env)
        return result
    if t is AST.Block:
        result = None
        for stmt in node.statements:
            result = evaluate(stmt, env)
        return result
    if t is AST.ExpressionStatement:
        return evaluate(node.expression, env)
    if t is AST.LetStatement:
        value = evaluate(node.value, env)
        env.define(node.name, value)
        return value
    if t is AST.AssignStatement:
        value = evaluate(node.value, env)
        _assign_target(node.target, value, env)
        return value
    if t is AST.Identifier:
        return env.get(node.value)
    if t is AST.NumberLiteral:
        return node.value
    if t is AST.StringLiteral:
        return node.value
    if t is AST.BooleanLiteral:
        return node.value
    if t is AST.NullLiteral:
        return None
    if t is AST.ArrayLiteral:
        return [evaluate(el, env) for el in node.elements]
    if t is AST.ObjectLiteral:
        return {prop.key: evaluate(prop.value, env) for prop in node.properties}
    if t is AST.PrefixExpression:
        right = evaluate(node.right, env)
        if node.operator == "!":
            return not is_truthy(right)
        if node.operator == "-":
            return -_expect_number(right)
        raise RuntimeErrorAegis(f"Unknown prefix operator {node.operator}")
    if t is AST.InfixExpression:
        left = evaluate(node.left, env)
        right = evaluate(node.right, env)
        op = node.operator
        if op == "+":
            return _binary_add(left, right)
        if op == "-":
            return _expect_number(left) - _expect_number(right)
        if op == "*":
            return _expect_number(left) * _expect_number(right)
        if op == "/":
            return _expect_number(left) / _expect_number(right)
        if op == "%":
            return _expect_number(left) % _expect_number(right)
        if op == "==":
            return deep_equal(left, right)
        if op == "!=":
            return not deep_equal(left, right)
        if op == "<":
            return _expect_number(left) < _expect_number(right)
        if op == ">":
            return _expect_number(left) > _expect_number(right)
        if op == "<=":
            return _expect_number(left) <= _expect_number(right)
        if op == ">=":
            return _expect_number(left) >= _expect_number(right)
        if op == "&&":
            return left if not is_truthy(left) else right
        if op == "||":
            return left if is_truthy(left) else right
        if op == "NOR":
            # Logical NOR: !(left || right). Preserve short-circuit semantics
            if is_truthy(left):
                return False
            return not is_truthy(right)
        if op == "IN":
            try:
                return left in right
            except Exception:
                return False
        raise RuntimeErrorAegis(f"Unknown operator {op}")
    if t is AST.CallExpression:
        callee = evaluate(node.callee, env)
        args = [evaluate(a, env) for a in node.args]
        return _call(callee, args, env)
    if t is AST.MemberExpression:
        obj = evaluate(node.object, env)
        return _get_member(obj, node.property)
    if t is AST.IndexExpression:
        coll = evaluate(node.collection, env)
        idx = evaluate(node.index, env)
        idx = _to_index(idx)
        return coll[idx]
    if t is AST.FunctionDefinition:
        return FunctionValue(name=node.name, params=node.params, body=node.body, env=env)
    if t is AST.ReturnStatement:
        value = evaluate(node.value, env) if node.value is not None else None
        raise ReturnSignal(value)
    if t is AST.IfStatement:
        test = evaluate(node.test, env)
        if is_truthy(test):
            return evaluate(node.consequent, env)
        if node.alternate is not None:
            return evaluate(node.alternate, env)
        return None
    if t is AST.WhileStatement:
        result = None
        while is_truthy(evaluate(node.test, env)):
            result = evaluate(node.body, env)
        return result
    raise RuntimeErrorAegis(f"Unknown node type {t}")


def _expect_number(value: Any) -> float:
    if isinstance(value, (int, float)):
        return float(value)
    raise RuntimeErrorAegis("Expected number")


def _to_index(value: Any) -> int:
    if isinstance(value, int):
        return value
    if isinstance(value, float) and float(value).is_integer():
        return int(value)
    raise RuntimeErrorAegis("Index must be an integer")


def _binary_add(a: Any, b: Any) -> Any:
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return a + b
    if isinstance(a, str) or isinstance(b, str):
        return str(a) + str(b)
    if isinstance(a, list) and isinstance(b, list):
        return a + b
    raise RuntimeErrorAegis("Unsupported + operands")


def _call(callee: Any, args: List[Any], env: Environment) -> Any:
    if isinstance(callee, NativeFunction):
        # Frame management happens inside NativeFunction.__call__
        return callee(args)
    if isinstance(callee, FunctionValue):
        frame_name = callee.name or "<anonymous>"
        enter_frame(frame_name)
        try:
            call_env = Environment(outer=callee.env)
            for i, name in enumerate(callee.params):
                call_env.define(name, args[i] if i < len(args) else None)
            try:
                return evaluate(callee.body, call_env)
            except ReturnSignal as rs:
                return rs.value
        finally:
            exit_frame()
    raise RuntimeErrorAegis("Attempt to call non-function")


def _get_member(obj: Any, prop: str) -> Any:
    if isinstance(obj, dict):
        return obj.get(prop)
    # native object with attributes
    if hasattr(obj, prop):
        return getattr(obj, prop)
    if isinstance(obj, list) and prop == "length":
        return len(obj)
    raise RuntimeErrorAegis(f"Property '{prop}' not found")


def assign_to_member(obj: Any, prop: str, value: Any) -> None:
    if isinstance(obj, dict):
        obj[prop] = value
        return
    if hasattr(obj, prop):
        setattr(obj, prop, value)
        return
    raise RuntimeErrorAegis("Cannot assign to property on this object")


def assign_to_index(coll: Any, idx: Any, value: Any) -> None:
    coll[idx] = value


def _assign_target(target: AST.Node, value: Any, env: Environment) -> None:
    import inspect
    if isinstance(target, AST.Identifier):
        env.assign(target.value, value)
        return
    if isinstance(target, AST.MemberExpression):
        obj = evaluate(target.object, env)
        assign_to_member(obj, target.property, value)
        return
    if isinstance(target, AST.IndexExpression):
        coll = evaluate(target.collection, env)
        idx = _to_index(evaluate(target.index, env))
        assign_to_index(coll, idx, value)
        return
    raise RuntimeErrorAegis("Invalid assignment target")


