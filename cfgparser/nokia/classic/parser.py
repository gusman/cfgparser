from __future__ import annotations

import re
import typing as t

from cfgparser.base.base import BaseParser
from cfgparser.nokia.classic.tokenizer import TokenBuilder
from cfgparser.path.path import DataPath
from cfgparser.tree.finder import Finder, Query
from cfgparser.tree.token import Token
from cfgparser.tree.transformer import Transformer


class Tree:
    def __init__(self) -> None:
        self.tokens: t.List[Token] = []

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

        # Calling a static class
        token = TokenBuilder.create_token(words, indent)

        if not token.name.startswith("exit"):
            self.tokens.append(token)

        return token

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

        parent.is_container = True
        for c in childs:
            existing_c = Finder(parent).find_token(c)
            if existing_c:
                Finder.recurse_merge_token(existing_c, c)
            else:
                parent.childs[c.id] = c

        self.tokens = [token for token in self.tokens if token not in childs]
        return None

    def is_complete(self) -> bool:
        return len(self.tokens) <= 1


class Parser(BaseParser):
    def __init__(self) -> None:
        self._tree = Tree()

    @staticmethod
    def identify(lines: t.Iterable) -> bool:
        ret = False
        for line in lines:
            if line.startswith("# TiMOS"):
                ret = True
                break

        return ret

    def parse(self, lines: t.Iterable) -> None:
        # loop until start line detected
        for line in lines:
            if line.startswith("# TiMOS"):
                break

        # start parsing line
        for line in lines:
            if line.startswith("# Finished"):
                break

            token = self._tree.scan_line(line)
            if token and token.name.startswith("exit"):
                self._tree.backparse_from_token(token.indent)

    def dumps(self) -> str:
        return Query(self._tree.tokens).dump_str()

    def to_dict(self) -> dict:
        return Query(self._tree.tokens).to_dict()

    def query(self, datapath: DataPath) -> list:
        tokens = Query(self._tree.tokens).query(datapath)
        return [Transformer(t).to_dict() for t in tokens]

    def get_paths(self) -> t.List[DataPath]:
        return Query(self._tree.tokens).get_paths()
