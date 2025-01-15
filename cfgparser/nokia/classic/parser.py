from __future__ import annotations

import re
import typing as t

from cfgparser.nokia.classic.token import Token
from cfgparser.nokia.classic.token import TokenBuilder


class Transformer:
    def __init__(self, token: Token):
        self.token = token

    def to_structured_text(self) -> str:
        def enclose_string(text: str) -> str:
            if " " in text:
                text = f'"{text}"'
            return text

        def traverse_text(token: Token):
            indent = ""
            for i in range(0, token.indent):
                indent += " "

            text = indent + enclose_string(token.name)
            if token.value:
                text += " " + enclose_string(token.value)

            if token.params:
                text = f"{text} {" ".join([enclose_string(t) for t in token.params])}"

            for c in token.childs.values():
                text += "\n"
                text += traverse_text(c)

            return text

        return traverse_text(self.token)

    def to_dict(self) -> dict:
        data: dict = {}

        def traverse_data(token: Token, data: dict):
            if token.childs:
                data[token.id] = {}
                for c in token.childs.values():
                    traverse_data(c, data[token.id])
            else:
                if token.params:
                    data[token.name] = [token.value] + token.params
                elif token.value:
                    data[token.name] = token.value
                else:
                    data[token.name] = ""

        traverse_data(self.token, data)
        return data


class Tree:
    def __init__(self):
        self.tokens = []

    @staticmethod
    def _tokenize_line(text: str) -> list:
        words = []
        text = text.strip()

        while text:
            if text.startswith('"'):
                match = re.match(r"\"(.+?)\"", text)

                if match:
                    text = text.replace(match.group(0), "", 1).lstrip()

                    # Remove double quotes before storing
                    words.append(match.group(0).replace('"', ""))
                    continue

            parts = text.split(" ", 1)
            if parts:
                words.append(parts[0])
                text = text.replace(parts[0], "", 1).lstrip()

        return words

    def scan_line(self, line) -> None | Token:
        line_clean = line.strip()
        if line_clean.startswith("#") or line.startswith("echo"):
            return None

        if len(line_clean) == 0:
            return None

        line_trimmed = line.rstrip()
        indent = len(line_trimmed) - len(line_trimmed.lstrip())

        words = self._tokenize_line(line_clean)
        # name = words[0]
        # value = None
        # params = []

        # if len(words) > 1:
        #     value = words[1]

        #     if name == "no":
        #         name, value = value, name

        # if len(words) > 2:
        #     params = words[2:]

        # token = Token(name, value, indent_sz, params)

        token = TokenBuilder.create_token(words, indent)
        if not token.name.startswith("exit"):
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
        ret = ""
        for idx, root_token in enumerate(self.tokens):
            ret += f"[root: {idx}]\n"
            ret += Transformer(root_token).to_structured_text()
            ret += "\n"

        return ret

    def to_dict(self) -> dict:
        lst = []

        for idx, root_token in enumerate(self.tokens):
            lst.append(Transformer(root_token).to_dict())

        ret = {}
        if lst:
            ret = lst[0]

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

    def to_dict(self) -> dict:
        return self._tree.to_dict()
