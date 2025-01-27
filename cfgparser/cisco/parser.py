from __future__ import annotations

import typing as t

from cfgparser.base.base import BaseParser
from cfgparser.cisco.tokenizer import INDENT_SZ
from cfgparser.cisco.tokenizer import TokenBuilder
from cfgparser.tree.finder import Finder
from cfgparser.tree.token import Token


class CiscoTree:
    def __init__(self):
        self.tokens = []
        self.indent_step_sz = INDENT_SZ

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

    def scan_line(self, line):
        words = line.strip().split(" ")
        words = [w for w in words if w]

        if not words:
            return None

        token, merged = self._lex_token(words, 0, self.tokens)
        if token and merged:
            return None

        if token:
            self.tokens.append(token)
            return None

        # Get root with the first word
        w = words[0].strip()
        curr_token = self._get_root_token(w, 0)

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

            curr_token = self._next_token(w, curr_token, indent_sz)
            words = words[1:]

        return None


class Parser(BaseParser):
    def __init__(self) -> None:
        super().__init__()
        self._tree = CiscoTree()

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
        prev_lines: t.List[str] = []
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
            line_stripped = line.strip()
            line_trimmed = line.rstrip()

            if line_stripped.startswith("!"):
                continue

            if line_stripped == "end":
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

            if line_stripped.startswith("no "):
                parts = line_stripped.split(" ")
                parts = parts[1:] + [parts[0]]
                line = " ".join(parts)

            curr_line = " ".join(prev_lines + [line])
            self._tree.scan_line(curr_line)

            prev_indent_sz = curr_indent_sz
            prev_line = line
