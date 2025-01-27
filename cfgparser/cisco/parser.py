from __future__ import annotations

import typing as t

from cfgparser.base.base import BaseParser
from cfgparser.cisco.tokenizer import TokenBuilder
from cfgparser.path.path import DataPath
from cfgparser.tree.finder import Finder, Query
from cfgparser.tree.token import Token
from cfgparser.tree.transformer import Transformer


class Tree:
    def __init__(self):
        self.tokens = []
        self.indent_step_sz = 1

    @staticmethod
    def _tokenize_last_word(name: str, curr_token: Token, indent_sz: int) -> None:
        if not curr_token.value and not curr_token.childs:
            curr_token.value = name

        elif curr_token.value and name != curr_token.value:
            curr_token.childs[curr_token.value] = Token(
                curr_token.value, None, indent_sz
            )
            curr_token.value = None
            curr_token.childs[name] = Token(name, None, indent_sz)

        elif name not in curr_token.childs:
            curr_token.childs[name] = Token(name, None, indent_sz)

        # What if word is already in curr token childs
        # How to handle it ??, Currently just ignored this condition

    @staticmethod
    def _next_token(name: str, curr_token: Token, indent_sz: int) -> Token:
        for c in curr_token.childs.values():
            if isinstance(c, Token) and c.name == name:
                next_token = c
                break
        else:
            if curr_token.value == name:
                curr_token.value = None
            curr_token.childs[name] = Token(name, None, indent_sz)
            next_token = curr_token.childs[name]

        return next_token

    def _get_root_token(self, name: str, indent_sz: int) -> Token:
        for tkn in self.tokens:
            if tkn.name == name:
                root_token = tkn
                break
        else:
            root_token = Token(name, None, indent_sz)
            self.tokens.append(root_token)

        return root_token

    def _lex_token(
        self, words: t.List[str], indent_sz: int, parents: t.List[Token]
    ) -> t.Tuple[None | Token, bool]:
        token = None
        merged = False

        token = TokenBuilder.create_token(words, indent_sz)
        if token:
            for dst_token in parents:
                merged = Finder.recurse_merge_token(dst_token, token)

        return token, merged

    def scan_line(self, line, indent_sz: int):
        words = line.strip().split(" ")
        words = [w for w in words if w]

        if not words:
            return None

        token, merged = self._lex_token(words, indent_sz, self.tokens)
        if token and merged:
            return None

        if token:
            self.tokens.append(token)
            return None

        # Get root with the first word
        w = words[0].strip()
        curr_token = self._get_root_token(w, indent_sz)

        if len(words) <= 1:
            return None

        words = words[1:]
        indent_ctr = 1
        while words:
            w = words[0].strip()
            indent_sz = indent_ctr * self.indent_step_sz

            token, merged = self._lex_token(words, indent_sz, [curr_token])
            if token and merged:
                break

            if token:
                if curr_token.value and w != curr_token.value:
                    curr_token.childs[curr_token.value] = Token(
                        curr_token.value, None, indent_sz
                    )
                    curr_token.value = None
                curr_token.childs[w] = token
                break

            if len(words) == 1:
                self._tokenize_last_word(w, curr_token, indent_sz)
                break
            else:
                curr_token = self._next_token(w, curr_token, indent_sz)
                words = words[1:]

        return None


class Parser(BaseParser):
    def __init__(self) -> None:
        self._tree = Tree()

    @staticmethod
    def identify(lines: t.Iterable) -> bool:
        ret = False

        for line in lines:
            if line.strip() == "!":
                ret = True
                break
        return ret

    @staticmethod
    def _move_to_start_of_config(lines: t.Iterable) -> None:
        for line in lines:
            if line.strip() == "!":
                break

    def parse(self, lines: t.Iterable) -> None:
        prev_lines = []
        prev_line = ""
        prev_indent_sz = 0
        indent_step_sz = 0

        # Loop untile line that can be parsed
        for line in lines:
            if line.strip() == "!":
                break

        # start parsing line
        banner_scan = False
        banner_lines = ""
        for line in lines:
            line_trimmed = line.rstrip()
            if line.startswith("!"):
                continue

            if line.strip() == "end":
                break

            if banner_scan:
                if line.count("^C") % 2 != 0:
                    line = banner_lines + line.strip()
                    banner_scan = False
                else:
                    banner_lines += line + "\n"
                    continue
            else:
                if line.startswith("banner") and (line.count("^C") % 2 != 0):
                    banner_scan = True
                    banner_lines += line + "\n"
                    continue

            curr_indent_sz = len(line_trimmed) - len(line_trimmed.lstrip())

            # Identify indent step size
            if prev_indent_sz == 0 and curr_indent_sz > prev_indent_sz:
                indent_step_sz = curr_indent_sz - prev_indent_sz
                self._tree.indent_step_sz = indent_step_sz

            if curr_indent_sz == 0:
                prev_lines = []
            elif curr_indent_sz > prev_indent_sz:
                prev_lines.append(prev_line)
            elif curr_indent_sz < prev_indent_sz:
                backward_indent_steps = (
                    prev_indent_sz - curr_indent_sz
                ) / indent_step_sz
                for _ in range(0, int(backward_indent_steps)):
                    prev_lines.pop()

            curr_line = " ".join(prev_lines + [line])
            self._tree.scan_line(curr_line, indent_sz=curr_indent_sz)

            prev_indent_sz = curr_indent_sz
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
