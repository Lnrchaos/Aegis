from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional, Any


@dataclass
class Node:
    line: int
    col: int


@dataclass
class Program(Node):
    body: List[Node]


@dataclass
class Block(Node):
    statements: List[Node]


@dataclass
class LetStatement(Node):
    name: str
    value: Node


@dataclass
class AssignStatement(Node):
    target: Node  # Identifier or Index or Member
    value: Node


@dataclass
class IfStatement(Node):
    test: Node
    consequent: Block
    alternate: Optional[Block]


@dataclass
class WhileStatement(Node):
    test: Node
    body: Block


@dataclass
class ReturnStatement(Node):
    value: Optional[Node]


@dataclass
class FunctionDefinition(Node):
    name: Optional[str]
    params: List[str]
    body: Block


@dataclass
class ExpressionStatement(Node):
    expression: Node


@dataclass
class Identifier(Node):
    value: str


@dataclass
class NumberLiteral(Node):
    value: Any


@dataclass
class StringLiteral(Node):
    value: str


@dataclass
class BooleanLiteral(Node):
    value: bool


@dataclass
class NullLiteral(Node):
    pass


@dataclass
class ArrayLiteral(Node):
    elements: List[Node]


@dataclass
class ObjectProperty(Node):
    key: str
    value: Node


@dataclass
class ObjectLiteral(Node):
    properties: List[ObjectProperty]


@dataclass
class PrefixExpression(Node):
    operator: str
    right: Node


@dataclass
class InfixExpression(Node):
    left: Node
    operator: str
    right: Node


@dataclass
class CallExpression(Node):
    callee: Node
    args: List[Node]


@dataclass
class IndexExpression(Node):
    collection: Node
    index: Node


@dataclass
class MemberExpression(Node):
    object: Node
    property: str


# New AST nodes for classes and error handling

@dataclass
class ClassDefinition(Node):
    name: str
    superclass: Optional[Identifier]
    methods: List[MethodDefinition]
    static_methods: List[MethodDefinition]


@dataclass
class MethodDefinition(Node):
    name: str
    params: List[str]
    body: Block
    is_static: bool = False
    is_override: bool = False


@dataclass
class NewExpression(Node):
    class_name: Identifier
    args: List[Node]


@dataclass
class SuperExpression(Node):
    method: str


@dataclass
class TryStatement(Node):
    try_block: Block
    catch_blocks: List[CatchBlock]
    finally_block: Optional[Block]


@dataclass
class CatchBlock(Node):
    exception_type: Optional[str]
    exception_var: Optional[str]
    body: Block


@dataclass
class ThrowStatement(Node):
    expression: Node


@dataclass
class AssertStatement(Node):
    condition: Node
    message: Optional[Node]


@dataclass
class AwaitExpression(Node):
    expression: Node


@dataclass
class AsyncFunctionDefinition(Node):
    name: Optional[str]
    params: List[str]
    body: Block


@dataclass
class ImportStatement(Node):
    module: str
    imports: List[str]  # specific imports, empty means import all
    alias: Optional[str]  # for "import x as y"


@dataclass
class ExportStatement(Node):
    name: str
    value: Optional[Node]  # None means re-export


@dataclass
class ForStatement(Node):
    init: Optional[Node]
    condition: Optional[Node]
    update: Optional[Node]
    body: Block


@dataclass
class ForInStatement(Node):
    variable: str
    iterable: Node
    body: Block


@dataclass
class SwitchStatement(Node):
    expression: Node
    cases: List[SwitchCase]
    default_case: Optional[Block]


@dataclass
class SwitchCase(Node):
    value: Optional[Node]  # None for default case
    body: Block


@dataclass
class BreakStatement(Node):
    pass


@dataclass
class ContinueStatement(Node):
    pass


@dataclass
class WithStatement(Node):
    resource: Node
    body: Block


@dataclass
class DeferStatement(Node):
    expression: Node