from __future__ import annotations

import typing as t

from cfgparser.base.base import BaseParser
from cfgparser.cisco import tokenizer
from cfgparser.tree.finder import Finder
from cfgparser.tree.token import Token


class CiscoTree:
    def __init__(self):
        self.tokens = []
        self.indent_step_sz = tokenizer.get_indent_step_sz()

    def set_indent_step_sz(self, step_sz: int) -> None:
        self.indent_step_sz = step_sz
        tokenizer.set_indent_step_sz(step_sz)

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

        token = tokenizer.create_token(words, indent_sz)
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


class CiscoParser(BaseParser):
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

    @staticmethod
    def _reposition_line_start_with_no(line: str, indent_sz: int) -> str:
        ret = line
        clean_line = line.strip()

        if clean_line.startswith("no "):
            parts = clean_line.split(" ")
            parts = parts[1:] + [parts[0]]

            indent_space = " " * indent_sz
            ret = indent_space + " ".join(parts)

        return ret

    @staticmethod
    def _scan_banner(
        banner_scan: bool, banner_line: str, line: str
    ) -> t.Tuple[bool, str]:
        if banner_scan:
            if line.count("^C") % 2 != 0:
                banner_line = banner_line + line.strip()
                banner_scan = False
            else:
                banner_line += line + "\n"
        else:
            if line.startswith("banner") and (line.count("^C") % 2 != 0):
                banner_scan = True
                banner_line += line + "\n"

        return banner_scan, banner_line

    def _construct_parent_lines(
        self,
        parent_lines: t.List[str],
        parent_line: str,
        curr_indent_sz: int,
        prev_indent_sz: int,
    ) -> t.List[str]:
        indent_step_sz = self._tree.indent_step_sz

        # Identify indent step size
        if prev_indent_sz == 0 and curr_indent_sz > prev_indent_sz:
            indent_step_sz = curr_indent_sz - prev_indent_sz
            self._tree.set_indent_step_sz(indent_step_sz)

        if curr_indent_sz == 0:
            parent_lines = []

        elif curr_indent_sz > prev_indent_sz:
            parent_lines.append(parent_line)

        elif curr_indent_sz < prev_indent_sz:
            backward_indent_steps = (prev_indent_sz - curr_indent_sz) / indent_step_sz
            for _ in range(0, int(backward_indent_steps)):
                parent_lines.pop()

        return parent_lines

    def parse(self, lines: t.Iterable) -> None:
        parent_lines: t.List[str] = []
        parent_line = ""
        prev_indent_sz = 0

        # Loop untile line that can be parsed
        for line in lines:
            if line.strip() == "!":
                break

        # start parsing line
        banner_scan = False
        banner_line = ""
        for line in lines:
            line_stripped = line.strip()
            line_trimmed = line.rstrip()

            # Skip comments
            if line_stripped.startswith("!"):
                continue

            # End of valid config line
            if line_stripped == "end":
                break

            # Check if the line is for banner text
            banner_scan, banner_line = self._scan_banner(banner_scan, banner_line, line)

            # Scan next line if current line part of banner
            if banner_scan:
                continue

            # Banner scan is done and use banner_lines as current line
            if banner_line:
                line = banner_line
                banner_line = ""

            curr_indent_sz = len(line_trimmed) - len(line_trimmed.lstrip())

            # Construct parent line if current line is indented
            parent_lines = self._construct_parent_lines(
                parent_lines, parent_line, curr_indent_sz, prev_indent_sz
            )

            # Reposition line "no" in line text
            line = self._reposition_line_start_with_no(line, curr_indent_sz)

            # Combine parent line and current line, in here text shall have no indent
            curr_line = " ".join(parent_lines + [line])

            # Scan line by separating words
            self._tree.scan_line(curr_line)

            # Update indent and parent line tracker
            prev_indent_sz = curr_indent_sz
            parent_line = line
