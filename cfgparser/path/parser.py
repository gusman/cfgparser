from __future__ import annotations

import typing as t

from cfgparser.path.path import DataPath
from cfgparser.path.path import Symbol
from cfgparser.path.path import Token
from cfgparser.path.path import TokenKind


class DataPathParser:
    def __init__(self, text: str):
        self.text: str = text
        self.tokens: t.List[Token] = []
        self.symbol = Symbol()
        self.path: None | DataPath = None

    def _scan(self, text: str) -> list:
        tokens = []

        val = ""
        for c in text:
            if c in self.symbol.maps:
                if val:
                    tokens.append(Token(val, TokenKind.TEXT))
                    val = ""
                tokens.append(Token(c, self.symbol.maps.get(c, TokenKind.TEXT)))
            else:
                val += c

        if val:
            tokens.append(Token(val, TokenKind.TEXT))

        return tokens

    @staticmethod
    def _extract_texts(tokens: t.List[Token]) -> list:
        ret = []

        str_flag = False
        text = ""
        for token in tokens:
            if token.kind == TokenKind.STR_QUOTE:
                str_flag = not str_flag
                continue

            if str_flag:
                text += token.value
                continue

            if token.kind == TokenKind.TEXT:
                text += token.value
                continue

            if token.kind == TokenKind.DELIMITER and text:
                ret.append(text)
                text = ""
        if text:
            ret.append(text)

        return ret

    def parse(self, clean_text: bool = True) -> DataPath:
        # Clean the text
        if clean_text:
            text = self.text.strip()
        else:
            text = self.text

        # Create tokens
        self.tokens = self._scan(text)

        # Extract path
        paths = self._extract_texts(self.tokens)

        # Store in path
        datapath = DataPath(paths, self.symbol)
        self.path = datapath

        return datapath
