from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Dict, Set


# Keyword handling: allow aliasing (e.g., def -> FN) and reserved domain terms
# Core language keywords and their token types
KEYWORD_TYPES: Dict[str, str] = {
    # 'let' is aliased to SET to support migration to 'set' for declarations
    "let": "SET",
    "set": "SET",
    "fn": "FN",
    "def": "FN",  # alias: def behaves like fn at the lexer level
    "return": "RETURN",
    "if": "IF",
    "else": "ELSE",
    "however": "HOWEVER",
    "unless": "UNLESS",
    "yet": "YET",
    "while": "WHILE",
    "until": "UNTIL",
    "true": "TRUE",
    "false": "FALSE",
    "null": "NULL",
    # class and OOP keywords
    "class": "CLASS",
    "new": "NEW",
    "super": "SUPER",
    "this": "THIS",
    "override": "OVERRIDE",
    "static": "STATIC",
    # error handling
    "try": "TRY",
    "catch": "CATCH",
    "finally": "FINALLY",
    "throw": "THROW",
    "assert": "ASSERT",
    # async/await
    "async": "ASYNC",
    "await": "AWAIT",
    # imports/exports
    "import": "IMPORT",
    "export": "EXPORT",
    "from": "FROM",
    "as": "AS",
    # additional control flow
    "for": "FOR",
    "in": "IN",
    "switch": "SWITCH",
    "case": "CASE",
    "default": "DEFAULT",
    "break": "BREAK",
    "continue": "CONTINUE",
    "with": "WITH",
    "defer": "DEFER",
    # word boolean operators / comparators
    "and": "AND",
    "or": "OR",
    "nor": "NOR",
    "not": "BANG",
    "is": "EQ",
    # contextual/reserved words
    "then": "THEN",
    "otherwise": "OTHERWISE",
    "when": "WHEN",
    "after": "AFTER",
    "because": "BECAUSE",
    "since": "SINCE",
    "without": "WITHOUT",
    "to": "TO",
    # cybersecurity contextual flow
    "trace": "TRACE",
    "monitor": "MONITOR",
    "quarantine": "QUARANTINE",
    "altert": "ALERT",
    "alert": "ALERT",
}

# Reserved cybersecurity/domain keywords (tokenized distinctly; parser may attach semantics later)
RESERVED_KEYWORDS: Set[str] = {
    "override", "firewall", "tunnel", "keylogger", "generate", "hash", "encrypt", "decrypt",
    "protect", "attack", "defend", "activate", "deactivate", "analyze", "contain", "payload",
    "load", "manipulate", "inject", "read", "write", "save", "corrupt", "break", "pause",
    "enter", "exit", "table", "brute",
}


@dataclass
class Token:
    type: str
    literal: str
    line: int
    col: int


SINGLE_CHAR_TOKENS = {
    "(": "LPAREN",
    ")": "RPAREN",
    "{": "LBRACE",
    "}": "RBRACE",
    "[": "LBRACKET",
    "]": "RBRACKET",
    ",": "COMMA",
    ":": "COLON",
    ";": "SEMICOLON",
    ".": "DOT",
    "+": "PLUS",
    "-": "MINUS",
    "*": "ASTERISK",
    "/": "SLASH",
    "%": "PERCENT",
    "!": "BANG",
    "<": "LT",
    ">": "GT",
    "=": "ASSIGN",
}


class Lexer:
    def __init__(self, source: str):
        self.source = source
        self.position = 0
        self.read_position = 0
        self.ch: Optional[str] = None
        self.line = 1
        self.col = 0
        self._read_char()

    def _read_char(self) -> None:
        if self.read_position >= len(self.source):
            self.ch = None
            return
        self.ch = self.source[self.read_position]
        self.position = self.read_position
        self.read_position += 1
        if self.ch == "\n":
            self.line += 1
            self.col = 0
        else:
            self.col += 1

    def _peek_char(self) -> Optional[str]:
        if self.read_position >= len(self.source):
            return None
        return self.source[self.read_position]

    def next_token(self) -> Token:
        self._skip_whitespace_and_comments()
        if self.ch is None:
            return Token("EOF", "", self.line, self.col)

        start_line, start_col = self.line, self.col
        # multi-char operators
        two = (self.ch or "") + (self._peek_char() or "")
        if two in {"==", "!=", "<=", ">=", "&&", "||"}:
            tok = Token({
                "==": "EQ",
                "!=": "NEQ",
                "<=": "LTE",
                ">=": "GTE",
                "&&": "AND",
                "||": "OR",
            }[two], two, start_line, start_col)
            self._read_char()
            self._read_char()
            return tok

        if self.ch in SINGLE_CHAR_TOKENS:
            literal = self.ch
            tok_type = SINGLE_CHAR_TOKENS[literal]
            self._read_char()
            return Token(tok_type, literal, start_line, start_col)

        if self.ch == '"':
            # Support block strings delimited by ""...""
            if self._peek_char() == '"':
                value = self._read_block_string()
            else:
                value = self._read_string()
            return Token("STRING", value, start_line, start_col)

        if self.ch.isdigit():
            value = self._read_number()
            return Token("NUMBER", value, start_line, start_col)

        if self.ch.isalpha() or self.ch == "_":
            ident = self._read_identifier()
            lt = ident.lower()
            if lt in KEYWORD_TYPES:
                tok_type = KEYWORD_TYPES[lt]
                # normalize literals for word operators to match interpreter semantics
                if lt == "and":
                    return Token("AND", "&&", start_line, start_col)
                if lt == "or":
                    return Token("OR", "||", start_line, start_col)
                if lt == "not":
                    return Token("BANG", "!", start_line, start_col)
                if lt == "is":
                    return Token("EQ", "==", start_line, start_col)
                if lt == "nor":
                    return Token("NOR", "NOR", start_line, start_col)
                if lt == "in":
                    return Token("IN", "IN", start_line, start_col)
                # others keep their original literal text
                return Token(tok_type, ident, start_line, start_col)
            if lt in RESERVED_KEYWORDS:
                return Token(lt.upper(), ident, start_line, start_col)
            return Token("IDENT", ident, start_line, start_col)

        # unknown char
        illegal = self.ch
        self._read_char()
        return Token("ILLEGAL", illegal, start_line, start_col)

    def _skip_whitespace_and_comments(self) -> None:
        while self.ch is not None:
            if self.ch in " \t\r\n":
                self._read_char()
                continue
            # line comment starting with #
            if self.ch == "#":
                while self.ch is not None and self.ch != "\n":
                    self._read_char()
                continue
            # line comment starting with //
            if self.ch == "/" and self._peek_char() == "/":
                while self.ch is not None and self.ch != "\n":
                    self._read_char()
                continue
            # line comment starting with ~
            if self.ch == "~":
                while self.ch is not None and self.ch != "\n":
                    self._read_char()
                continue
            break

    def _read_string(self) -> str:
        # consume opening quote
        self._read_char()
        chars = []
        while self.ch is not None and self.ch != '"':
            if self.ch == "\\":
                self._read_char()
                if self.ch is None:
                    break
                escapes = {
                    'n': '\n', 'r': '\r', 't': '\t', '"': '"', "'": "'", "\\": "\\",
                }
                chars.append(escapes.get(self.ch, self.ch))
            else:
                chars.append(self.ch)
            self._read_char()
        # consume closing quote
        if self.ch == '"':
            self._read_char()
        return "".join(chars)

    def _read_block_string(self) -> str:
        # consume opening double quotes ""
        self._read_char()  # first '"'
        self._read_char()  # second '"'
        chars = []
        while self.ch is not None:
            # end delimiter: two consecutive quotes
            if self.ch == '"' and self._peek_char() == '"':
                self._read_char()  # first closing '"'
                self._read_char()  # second closing '"'
                break
            if self.ch == "\\":
                # allow basic escapes inside block strings too
                self._read_char()
                if self.ch is None:
                    break
                escapes = {
                    'n': '\n', 'r': '\r', 't': '\t', '"': '"', "'": "'", "\\": "\\",
                }
                chars.append(escapes.get(self.ch, self.ch))
            else:
                chars.append(self.ch)
            self._read_char()
        return "".join(chars)

    def _read_number(self) -> str:
        start = self.position
        has_dot = False
        while self.ch is not None and (self.ch.isdigit() or (self.ch == "." and not has_dot)):
            if self.ch == ".":
                has_dot = True
            self._read_char()
        return self.source[start:self.position]

    def _read_identifier(self) -> str:
        start = self.position
        while self.ch is not None and (self.ch.isalnum() or self.ch == "_"):
            self._read_char()
        return self.source[start:self.position]


