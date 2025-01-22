from __future__ import annotations

import typing as t

from cfgparser.path.path import DataPath
from cfgparser.tree.finder import Query
from cfgparser.tree.token import Token
from cfgparser.tree.transformer import Transformer


class Tree:
    def __init__(self):
        self.tokens = []

    @staticmethod
    def _tokenize_last_word(name: str, curr_token: Token) -> None:
        if not curr_token.value and not curr_token.childs:
            curr_token.value = name

        elif curr_token.value and name != curr_token.value:
            curr_token.childs[curr_token.value] = Token(curr_token.value, None, 0)
            curr_token.value = ""
            curr_token.childs[name] = Token(name, None, 0)

        elif name not in curr_token.childs:
            curr_token.childs[name] = Token(name, None, 0)

        # What if word is already in curr token childs

    @staticmethod
    def _next_token(name: str, curr_token: Token) -> Token:
        for c in curr_token.childs.values():
            if isinstance(c, Token) and c.name == name:
                next_token = c
                break
        else:
            if curr_token.value == name:
                curr_token.value = ""
            curr_token.childs[name] = Token(name, None, 0)
            next_token = curr_token.childs[name]

        return next_token

    def _get_root_token(self, name: str, indent_size) -> Token:
        for tkn in self.tokens:
            if tkn.name == name:
                root_token = tkn
                break
        else:
            root_token = Token(name, None, indent_size)
            self.tokens.append(root_token)

        return root_token

    def scan_line(self, line, indent_size: int):
        words = line.strip().split(" ")
        words = [w for w in words if w]

        if not words:
            return None

        # Get root with the first word
        w = words[0]
        curr_token = self._get_root_token(w, indent_size)

        if len(words) <= 1:
            return None

        words = words[1:]
        while words:
            indent_size += 1
            w = words[0]

            if len(words) == 1:
                self._tokenize_last_word(w, curr_token)
                break
            else:
                curr_token = self._next_token(w, curr_token)
                words = words[1:]

        return None


class Parser:
    def __init__(self) -> None:
        self._tree = Tree()

    def parse(self, lines: t.Iterable) -> None:
        # Move until start line detected
        # parser = Parser()

        prev_lines = []
        prev_line = ""
        prev_indent = 0
        indent_step_sz = 0

        for line in lines:
            line_trimmed = line.rstrip()
            if line == "!":
                continue

            curr_indent = len(line_trimmed) - len(line_trimmed.lstrip())

            if prev_indent == 0 and curr_indent > prev_indent:
                indent_step_sz = curr_indent - prev_indent

            if curr_indent == 0:
                prev_lines = []
            elif curr_indent > prev_indent:
                prev_lines.append(prev_line)
            elif curr_indent < prev_indent:
                backward_indent_steps = (prev_indent - curr_indent) / indent_step_sz
                for _ in range(0, int(backward_indent_steps)):
                    prev_lines.pop()

            # print(curr_indent, prev_indent)
            # print(curr_line)
            curr_line = " ".join(prev_lines + [line])
            self._tree.scan_line(curr_line, indent_size=curr_indent)

            prev_indent = curr_indent
            prev_line = line

    def dumps(self) -> str:
        return Query(self._tree.tokens).dump_str()

    def to_dict(self) -> dict:
        return Query(self._tree.tokens).to_dict()

    def query(self, datapath: DataPath) -> list:
        tokens = Query(self._tree.tokens).query(datapath)
        return [Transformer(t).to_dict() for t in tokens]

    def get_paths(self) -> t.List[DataPath]:
        return Query(self._tree.tokens).get_paths()
