from __future__ import annotations

import dataclasses
import typing as t


@dataclasses.dataclass
class Token:
    name: str = ""
    value: str = ""
    indent: int = 0
    params: list = dataclasses.field(default_factory=list)
    childs: list = dataclasses.field(default_factory=dict)

    @property
    def id(self):
        if isinstance(self.value, str):
            return f"{self.name} {self.value}"
        else:
            return self.name


class Tree:
    def __init__(self):
        self.tokens = []

    def scan_line(self, line) -> None | Token:
        line_clean = line.strip()
        if line_clean.startswith("#") or line.startswith("echo"):
            return None

        if len(line_clean) == 0:
            return None

        line_trimmed = line.rstrip()
        indent_sz = len(line_trimmed) - len(line_trimmed.lstrip())
        tokens = line_clean.split(" ")

        name = tokens[0]
        value = None
        params = []

        if len(tokens) > 1:
            value = tokens[1]

        if len(tokens) > 2:
            params = tokens[2:]

        token = Token(name, value, indent_sz, params)
        if not name.startswith("exit"):
            self.tokens.append(token)

        return token

    @staticmethod
    def _is_token_same(token_a: Token, token_b: Token) -> bool:
        return (
            (token_a.name == token_b.name)
            and (token_a.indent == token_b.indent)
            and (token_a.value == token_b.value)
        )

    def _recurse_merge_dict_of_child(self, token_dst: Token, token_src: Token) -> None:
        if not self._is_token_same(token_dst, token_src):
            return None

        if not token_src.childs:
            return None

        for token_id, src_val in token_src.childs.items():
            if token_id not in token_dst.childs:
                token_dst.childs[token_id] = src_val
            else:
                dst_val = token_dst.childs[token_id]

                if not isinstance(dst_val, Token) and isinstance(src_val, Token):
                    token_dst.childs[token_id] = src_val
                elif (
                    isinstance(dst_val, Token)
                    and not dst_val.childs
                    and isinstance(src_val, Token)
                    and src_val.childs
                ):
                    token_dst.childs[token_id] = src_val
                elif (
                    isinstance(dst_val, Token)
                    and dst_val.childs
                    and isinstance(src_val, Token)
                    and src_val.childs
                ):
                    self._recurse_merge_dict_of_child(dst_val, src_val)
                else:
                    pass

        return None

    def backparse_from_token(self, indent_sz: int) -> None:
        childs = []
        parent: Token | None = None

        for token in reversed(self.tokens):
            if indent_sz < token.indent:
                childs.append(token)
            elif indent_sz == token.indent:
                parent = token
                break

        if not parent:
            return None

        for c in childs:
            existing_c = self._find_token(parent, c)
            if existing_c:
                self._recurse_merge_dict_of_child(existing_c, c)
            else:
                parent.childs[c.id] = c

        self.tokens = [token for token in self.tokens if token not in childs]
        return None

    def _find_token(self, token_tree: Token, token: Token) -> None | Token:
        if self._is_token_same(token_tree, token):
            return token_tree

        for c in token_tree.childs.values():
            ret = self._find_token(c, token)
            if ret:
                return ret
        return None

    def _traverse_dump_str(self, token: Token) -> str:
        indent = ""
        for i in range(0, token.indent):
            indent += " "

        text = indent + token.id
        if token.params:
            text = f"{text} {" ".join(token.params)}"

        for c in token.childs.values():
            text += "\n"
            text += self._traverse_dump_str(c)

        return text

    def dump_str(self) -> str:
        if not self.tokens:
            return ""

        return self._traverse_dump_str(self.tokens[0])

    def is_complete(self) -> bool:
        return len(self.tokens) <= 1


class Parser:
    def __init__(self):
        self._tree = Tree()

    def parse(self, lines: t.Iterable) -> None:
        for line in lines:
            token = self._tree.scan_line(line)

            if token and token.name.startswith("exit"):
                self._tree.backparse_from_token(token.indent)

    def dumps(self) -> str:
        return self._tree.dump_str()
