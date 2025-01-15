from __future__ import annotations

import typing as t


class Token:
    def __init__(
        self,
        name: str,
        value: str,
        indent: int,
        params: t.Optional[t.List] = None,
        childs: t.Optional[t.Dict] = None,
    ):
        self.name: str = name
        self.value: str = value
        self.indent: int = indent
        self.params: list = []
        self.childs: dict = {}

        if params:
            self.params = params

        if childs:
            self.childs = childs

    @property
    def id(self):
        if isinstance(self.value, str):
            return f"{self.name} {self.value}"
        else:
            return self.name

    def is_attr_same(self, token: Token) -> bool:
        return (
            (self.name == token.name)
            and (self.indent == token.indent)
            and (self.value == token.value)
        )

    def find_token(self, token: Token) -> None | Token:
        def recurse_find(token_tree: Token, token: Token):
            if token_tree.is_attr_same(token):
                return token_tree

            for c in token_tree.childs.values():
                ret = recurse_find(c, token)
                if ret:
                    return ret
            return None

        return recurse_find(self, token)


class Transformer:
    def __init__(self, token: Token):
        self.token = token

    def to_structured_text(self) -> str:
        def traverse_text(token):
            indent = ""
            for i in range(0, token.indent):
                indent += " "

            text = indent + token.id
            if token.params:
                text = f"{text} {" ".join(token.params)}"

            for c in token.childs.values():
                text += "\n"
                text += traverse_text(c)

            return text

        return traverse_text(self.token)


class Tree:
    def __init__(self):
        self.tokens: t.List[Token] = []

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

    def _recurse_merge_dict_of_child(self, token_dst: Token, token_src: Token) -> None:
        if not token_dst.is_attr_same(token_src):
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
            existing_c = parent.find_token(c)
            if existing_c:
                self._recurse_merge_dict_of_child(existing_c, c)
            else:
                parent.childs[c.id] = c

        self.tokens = [token for token in self.tokens if token not in childs]
        return None

    def is_complete(self) -> bool:
        return len(self.tokens) <= 1

    def dump_str(self) -> str:
        if not self.tokens:
            return ""

        ret = ""
        for idx, root_token in enumerate(self.tokens):
            ret += f"[root: {idx}]\n"
            ret += Transformer(root_token).to_structured_text()
            ret += "\n"

        return ret


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
