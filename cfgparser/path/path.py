from __future__ import annotations

import dataclasses
import typing as t
from enum import Enum


class TokenKind(Enum):
    TEXT = 1
    DELIMITER = 2
    STR_QUOTE = 3


@dataclasses.dataclass
class Token:
    value: str = ""
    kind: TokenKind = TokenKind.TEXT


class Symbol:
    def __init__(self, delimiter: str = "/"):
        self.delimiter = "/"
        self.maps = {
            delimiter: TokenKind.DELIMITER,
            '"': TokenKind.STR_QUOTE,
        }


class DataPath:
    def __init__(self, paths: t.List[str] | None = None, symbol: Symbol | None = None):
        if paths:
            self.paths: t.List = paths
        else:
            self.paths = []

        if symbol:
            self.symbol = symbol
        else:
            self.symbol = Symbol()

    def add(self, path_part: str):
        self.paths.append(path_part)

    def __str__(self):
        return f"DataPath, paths: {self.paths}, delimiter: {self.symbol.delimiter}"
