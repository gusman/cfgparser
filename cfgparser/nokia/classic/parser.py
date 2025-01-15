from __future__ import annotations

import dataclasses


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


class Parser:
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
    def is_token_same(token_a: Token, token_b: Token) -> bool:
        return (
            (token_a.name == token_b.name)
            and (token_a.indent == token_b.indent)
            and (token_a.value == token_b.value)
        )

    def recursive_merge_dict_of_child(self, token_dst: Token, token_src: Token):
        if not self.is_token_same(token_dst, token_src):
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
                    self.recursive_merge_dict_of_child(dst_val, src_val)
                else:
                    pass

        return None

    def __print_tokens(self):
        for idx, token in enumerate(self.tokens):
            print(f"[{idx}]")
            self.traverse_print(token)

    def backtrack_parse_container(self, indent_sz: int) -> None:
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
            existing_c = self.find_existing_token(parent, c)
            if existing_c:
                self.recursive_merge_dict_of_child(existing_c, c)
            else:
                parent.childs[c.id] = c

        self.tokens = [token for token in self.tokens if token not in childs]

        return None

    def find_existing_token(self, token_tree: Token, token: Token) -> None | Token:
        if self.is_token_same(token_tree, token):
            return token_tree

        for c in token_tree.childs.values():
            ret = self.find_existing_token(c, token)
            if ret:
                return ret

        return None

    def traverse_print(self, token: Token):
        indent = ""
        for i in range(0, token.indent):
            indent += " "

        text = indent + token.id
        if token.params:
            text = f"{text} {" ".join(token.params)}"
        print(text)

        for c in token.childs.values():
            self.traverse_print(c)

    def traverse_dump(self) -> None:
        if not self.tokens:
            return None

        self.traverse_print(self.tokens[0])
        return None

    def is_complete(self) -> bool:
        return len(self.tokens) <= 1


def parse(fd):
    parser = Parser()

    for line in fd:
        token = parser.scan_line(line)
        if token and token.name.startswith("exit"):
            parser.backtrack_parse_container(token.indent)

    print("-----------------------------------------------")
    print(" Final Dump")
    print("-----------------------------------------------")
    parser.traverse_dump()

    print("-----------------------------------------------")
    print("Is Complete: ", parser.is_complete())
    print("-----------------------------------------------")
