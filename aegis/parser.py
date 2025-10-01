from __future__ import annotations
from typing import List, Optional, Callable, Dict
from .lexer import Lexer, Token
from .ast_nodes import (
    Program, Block, LetStatement, AssignStatement, IfStatement, WhileStatement,
    ReturnStatement, FunctionDefinition, ExpressionStatement, Identifier,
    NumberLiteral, StringLiteral, BooleanLiteral, NullLiteral, ArrayLiteral,
    ObjectLiteral, ObjectProperty, PrefixExpression, InfixExpression,
    CallExpression, IndexExpression, MemberExpression, Node
)


PRECEDENCES: Dict[str, int] = {
    "OR": 1,
    "NOR": 1,
    "AND": 2,
    "EQ": 3, "NEQ": 3, "IN": 3,
    "LT": 4, "GT": 4, "LTE": 4, "GTE": 4,
    "PLUS": 5, "MINUS": 5,
    "ASTERISK": 6, "SLASH": 6, "PERCENT": 6,
    "DOT": 7, "LBRACKET": 7, "LPAREN": 7,
}


class ParseError(Exception):
    pass


class Parser:
    def __init__(self, lexer: Lexer):
        self.lexer = lexer
        self.cur: Token = self.lexer.next_token()
        self.peek: Token = self.lexer.next_token()

        self.prefix_parse_fns: Dict[str, Callable[[], Node]] = {}
        self.infix_parse_fns: Dict[str, Callable[[Node], Node]] = {}

        self._register_prefix("IDENT", self._parse_identifier)
        self._register_prefix("NUMBER", self._parse_number)
        self._register_prefix("STRING", self._parse_string)
        self._register_prefix("TRUE", self._parse_boolean)
        self._register_prefix("FALSE", self._parse_boolean)
        self._register_prefix("NULL", self._parse_null)
        self._register_prefix("BANG", self._parse_prefix)
        self._register_prefix("MINUS", self._parse_prefix)
        self._register_prefix("LPAREN", self._parse_grouped)
        self._register_prefix("LBRACKET", self._parse_array)
        self._register_prefix("LBRACE", self._parse_object)
        self._register_prefix("FN", self._parse_function_literal)

        for t in ["PLUS", "MINUS", "ASTERISK", "SLASH", "PERCENT",
                  "EQ", "NEQ", "LT", "GT", "LTE", "GTE",
                  "AND", "OR", "NOR", "IN"]:
            self._register_infix(t, self._parse_infix)
        self._register_infix("LPAREN", self._parse_call)
        self._register_infix("LBRACKET", self._parse_index)
        self._register_infix("DOT", self._parse_member)

    def _advance(self) -> None:
        self.cur = self.peek
        self.peek = self.lexer.next_token()

    def _expect(self, token_type: str) -> Token:
        if self.cur.type != token_type:
            raise ParseError(f"Expected {token_type}, got {self.cur.type} at {self.cur.line}:{self.cur.col}")
        tok = self.cur
        self._advance()
        return tok

    def _current_precedence(self) -> int:
        return PRECEDENCES.get(self.cur.type, 0)

    def _peek_precedence(self) -> int:
        return PRECEDENCES.get(self.peek.type, 0)

    def _register_prefix(self, token_type: str, fn: Callable[[], Node]) -> None:
        self.prefix_parse_fns[token_type] = fn

    def _register_infix(self, token_type: str, fn: Callable[[Node], Node]) -> None:
        self.infix_parse_fns[token_type] = fn

    def parse_program(self) -> Program:
        statements: List[Node] = []
        start_line, start_col = self.cur.line, self.cur.col
        while self.cur.type != "EOF":
            stmt = self._parse_statement()
            if stmt is not None:
                statements.append(stmt)
            # optional semicolon handling
            if self.cur.type == "SEMICOLON":
                self._advance()
        return Program(line=start_line, col=start_col, body=statements)

    def _parse_statement(self) -> Node:
        if self.cur.type == "LET":
            return self._parse_let_statement()
        if self.cur.type == "SET":
            return self._parse_set_statement()
        if self.cur.type == "RETURN":
            return self._parse_return_statement()
        if self.cur.type == "IF":
            return self._parse_if_statement()
        if self.cur.type == "UNLESS":
            return self._parse_unless_statement()
        if self.cur.type == "UNTIL":
            return self._parse_until_statement()
        if self.cur.type == "WHILE":
            return self._parse_while_statement()
        if self.cur.type == "FN":
            # function declaration statement: fn name(...) { ... }
            return self._parse_function_declaration_statement()
        # expression statement
        expr = self._parse_expression(0)
        node = ExpressionStatement(line=expr.line, col=expr.col, expression=expr)
        if self.cur.type == "SEMICOLON":
            self._advance()
        return node

    def _parse_block(self) -> Block:
        start_line, start_col = self.cur.line, self.cur.col
        self._expect("LBRACE")
        statements: List[Node] = []
        while self.cur.type != "RBRACE" and self.cur.type != "EOF":
            stmt = self._parse_statement()
            statements.append(stmt)
            if self.cur.type == "SEMICOLON":
                self._advance()
        self._expect("RBRACE")
        return Block(line=start_line, col=start_col, statements=statements)

    def _parse_let_statement(self) -> LetStatement:
        start_line, start_col = self.cur.line, self.cur.col
        self._expect("LET")
        name_tok = self._expect("IDENT")
        self._expect("ASSIGN")
        value = self._parse_expression(0)
        if self.cur.type == "SEMICOLON":
            self._advance()
        return LetStatement(line=start_line, col=start_col, name=name_tok.literal, value=value)

    def _parse_set_statement(self) -> AssignStatement:
        start_line, start_col = self.cur.line, self.cur.col
        self._expect("SET")
        target = self._parse_assignment_target()
        self._expect("ASSIGN")
        value = self._parse_expression(0)
        if self.cur.type == "SEMICOLON":
            self._advance()
        return AssignStatement(line=start_line, col=start_col, target=target, value=value)

    def _parse_assignment_target(self) -> Node:
        expr = self._parse_expression(7)  # parse up to member/index
        if not isinstance(expr, (Identifier, IndexExpression, MemberExpression)):
            raise ParseError(f"Invalid assignment target at {self.cur.line}:{self.cur.col}")
        return expr

    def _parse_return_statement(self) -> ReturnStatement:
        start_line, start_col = self.cur.line, self.cur.col
        self._expect("RETURN")
        if self.cur.type in ("SEMICOLON", "RBRACE"):
            return ReturnStatement(line=start_line, col=start_col, value=None)
        value = self._parse_expression(0)
        if self.cur.type == "SEMICOLON":
            self._advance()
        return ReturnStatement(line=start_line, col=start_col, value=value)

    def _parse_if_statement(self) -> IfStatement:
        start_line, start_col = self.cur.line, self.cur.col
        self._expect("IF")
        self._expect("LPAREN")
        test = self._parse_expression(0)
        self._expect("RPAREN")
        # Optional THEN before block
        if self.cur.type == "THEN":
            self._advance()
        consequent = self._parse_block()
        # Collect zero or more 'HOWEVER (cond) { ... }'
        elif_list: List[tuple[Node, Block]] = []
        while self.cur.type == "HOWEVER":
            self._advance()
            self._expect("LPAREN")
            h_test = self._parse_expression(0)
            self._expect("RPAREN")
            h_block = self._parse_block()
            elif_list.append((h_test, h_block))
        # Optional final else/yet
        final_alt: Optional[Block] = None
        if self.cur.type in ("ELSE", "YET", "OTHERWISE"):
            self._advance()
            final_alt = self._parse_block()

        # Build nested chain if we have however-clauses
        alternate: Optional[Block] = None
        if elif_list:
            # Build from the last however upward
            cur_if: IfStatement
            last_test, last_block = elif_list[-1]
            cur_if = IfStatement(line=start_line, col=start_col, test=last_test, consequent=last_block, alternate=final_alt)
            # Wrap remaining however clauses
            for t, b in reversed(elif_list[:-1]):
                cur_if = IfStatement(line=start_line, col=start_col, test=t, consequent=b, alternate=Block(line=start_line, col=start_col, statements=[cur_if]))
            # Set base alternate to a block containing the chain
            alternate = Block(line=start_line, col=start_col, statements=[cur_if])
        else:
            alternate = final_alt
        return IfStatement(line=start_line, col=start_col, test=test, consequent=consequent, alternate=alternate)

    def _parse_unless_statement(self) -> IfStatement:
        start_line, start_col = self.cur.line, self.cur.col
        self._expect("UNLESS")
        self._expect("LPAREN")
        test = self._parse_expression(0)
        self._expect("RPAREN")
        # Invert condition using prefix '!'
        inv = PrefixExpression(line=start_line, col=start_col, operator="!", right=test)
        # Optional THEN before block
        if self.cur.type == "THEN":
            self._advance()
        consequent = self._parse_block()
        alternate: Optional[Block] = None
        if self.cur.type in ("ELSE", "YET", "OTHERWISE"):
            self._advance()
            alternate = self._parse_block()
        return IfStatement(line=start_line, col=start_col, test=inv, consequent=consequent, alternate=alternate)

    def _parse_until_statement(self) -> WhileStatement:
        start_line, start_col = self.cur.line, self.cur.col
        self._expect("UNTIL")
        self._expect("LPAREN")
        test = self._parse_expression(0)
        self._expect("RPAREN")
        # while not test { ... }
        inv = PrefixExpression(line=start_line, col=start_col, operator="!", right=test)
        body = self._parse_block()
        return WhileStatement(line=start_line, col=start_col, test=inv, body=body)

    def _parse_while_statement(self) -> WhileStatement:
        start_line, start_col = self.cur.line, self.cur.col
        self._expect("WHILE")
        self._expect("LPAREN")
        test = self._parse_expression(0)
        self._expect("RPAREN")
        body = self._parse_block()
        return WhileStatement(line=start_line, col=start_col, test=test, body=body)

    def _parse_function_declaration_statement(self):
        # desugar to set name = fn(...) { ... } using declare-if-undefined semantics
        start_line, start_col = self.cur.line, self.cur.col
        self._expect("FN")
        name_tok = self._expect("IDENT")
        params, body = self._parse_function_tail()
        func = FunctionDefinition(line=start_line, col=start_col, name=name_tok.literal, params=params, body=body)
        ident = Identifier(line=name_tok.line, col=name_tok.col, value=name_tok.literal)
        return AssignStatement(line=start_line, col=start_col, target=ident, value=func)

    def _parse_expression(self, precedence: int) -> Node:
        prefix = self.prefix_parse_fns.get(self.cur.type)
        if prefix is None:
            raise ParseError(f"No prefix parse function for {self.cur.type} at {self.cur.line}:{self.cur.col}")
        left = prefix()

        while self.cur.type not in ("SEMICOLON", "EOF", "RBRACE") and precedence < self._current_precedence():
            infix = self.infix_parse_fns.get(self.cur.type)
            if infix is None:
                return left
            left = infix(left)
        return left

    # prefix parse fns
    def _parse_identifier(self) -> Identifier:
        tok = self._expect("IDENT")
        return Identifier(line=tok.line, col=tok.col, value=tok.literal)

    def _parse_number(self) -> NumberLiteral:
        tok = self._expect("NUMBER")
        lit = tok.literal
        if "." in lit:
            val = float(lit)
        else:
            try:
                val = int(lit)
            except ValueError:
                val = float(lit)
        return NumberLiteral(line=tok.line, col=tok.col, value=val)

    def _parse_string(self) -> StringLiteral:
        tok = self._expect("STRING")
        return StringLiteral(line=tok.line, col=tok.col, value=tok.literal)

    def _parse_boolean(self) -> BooleanLiteral:
        if self.cur.type == "TRUE":
            tok = self._expect("TRUE")
            return BooleanLiteral(line=tok.line, col=tok.col, value=True)
        tok = self._expect("FALSE")
        return BooleanLiteral(line=tok.line, col=tok.col, value=False)

    def _parse_null(self) -> NullLiteral:
        tok = self._expect("NULL")
        return NullLiteral(line=tok.line, col=tok.col)

    def _parse_prefix(self) -> PrefixExpression:
        tok = self.cur
        self._advance()
        right = self._parse_expression(7)
        return PrefixExpression(line=tok.line, col=tok.col, operator=tok.literal, right=right)

    def _parse_grouped(self) -> Node:
        self._expect("LPAREN")
        expr = self._parse_expression(0)
        self._expect("RPAREN")
        return expr

    def _parse_array(self) -> ArrayLiteral:
        start_line, start_col = self.cur.line, self.cur.col
        self._expect("LBRACKET")
        elements: List[Node] = []
        if self.cur.type != "RBRACKET":
            while True:
                elements.append(self._parse_expression(0))
                if self.cur.type == "COMMA":
                    self._advance()
                    continue
                break
        self._expect("RBRACKET")
        return ArrayLiteral(line=start_line, col=start_col, elements=elements)

    def _parse_object(self) -> ObjectLiteral:
        start_line, start_col = self.cur.line, self.cur.col
        self._expect("LBRACE")
        props: List[ObjectProperty] = []
        if self.cur.type != "RBRACE":
            while True:
                if self.cur.type == "IDENT":
                    key_tok = self._expect("IDENT")
                    key = key_tok.literal
                elif self.cur.type == "STRING":
                    key_tok = self._expect("STRING")
                    key = key_tok.literal
                else:
                    raise ParseError(f"Invalid object key at {self.cur.line}:{self.cur.col}")
                self._expect("COLON")
                value = self._parse_expression(0)
                props.append(ObjectProperty(line=key_tok.line, col=key_tok.col, key=key, value=value))
                if self.cur.type == "COMMA":
                    self._advance()
                    continue
                break
        self._expect("RBRACE")
        return ObjectLiteral(line=start_line, col=start_col, properties=props)

    def _parse_function_literal(self) -> FunctionDefinition:
        start_line, start_col = self.cur.line, self.cur.col
        self._expect("FN")
        params, body = self._parse_function_tail()
        return FunctionDefinition(line=start_line, col=start_col, name=None, params=params, body=body)

    def _parse_function_tail(self):
        params: List[str] = []
        self._expect("LPAREN")
        if self.cur.type != "RPAREN":
            while True:
                name_tok = self._expect("IDENT")
                params.append(name_tok.literal)
                if self.cur.type == "COMMA":
                    self._advance()
                    continue
                break
        self._expect("RPAREN")
        body = self._parse_block()
        return params, body

    # infix parse fns
    def _parse_infix(self, left: Node) -> InfixExpression:
        op_tok = self.cur
        precedence = self._current_precedence()
        self._advance()
        right = self._parse_expression(precedence)
        return InfixExpression(line=op_tok.line, col=op_tok.col, left=left, operator=op_tok.literal, right=right)

    def _parse_call(self, left: Node) -> CallExpression:
        lparen = self._expect("LPAREN")
        args: List[Node] = []
        if self.cur.type != "RPAREN":
            while True:
                args.append(self._parse_expression(0))
                if self.cur.type == "COMMA":
                    self._advance()
                    continue
                break
        self._expect("RPAREN")
        return CallExpression(line=lparen.line, col=lparen.col, callee=left, args=args)

    def _parse_index(self, left: Node) -> IndexExpression:
        lbrack = self._expect("LBRACKET")
        index = self._parse_expression(0)
        self._expect("RBRACKET")
        return IndexExpression(line=lbrack.line, col=lbrack.col, collection=left, index=index)

    def _parse_member(self, left: Node) -> MemberExpression:
        dot = self._expect("DOT")
        name_tok = self._expect("IDENT")
        return MemberExpression(line=dot.line, col=dot.col, object=left, property=name_tok.literal)


def parse(source: str) -> Program:
    parser = Parser(Lexer(source))
    return parser.parse_program()


