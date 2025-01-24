from __future__ import annotations

import typing as t
from abc import abstractmethod

from loguru import logger

from cfgparser.path.path import DataPath
from cfgparser.tree.token import Token


class BaseParser:
    def __init__(self) -> None:
        self.tokens: t.List[Token] = []

    @staticmethod
    @abstractmethod
    def identify(lines: t.Iterable) -> bool: ...

    @abstractmethod
    def parse(self, lines: t.Iterable) -> None: ...

    @abstractmethod
    def dumps(self) -> str: ...

    @abstractmethod
    def to_dict(self) -> dict: ...

    @abstractmethod
    def query(self, datapath: DataPath) -> list: ...

    @abstractmethod
    def get_paths(self) -> t.List[DataPath]: ...


class NullParser(BaseParser):
    def __init__(self) -> None:
        return None

    @staticmethod
    def _show_message() -> None:
        logger.info(
            "This is null parser and cannot parse and other operation, you need to use correct parser"
        )

    def identify(self, lines: t.Iterable) -> bool:
        return False

    def parse(self, lines: t.Iterable) -> None:
        self._show_message()
        return None

    def dumps(self) -> str:
        self._show_message()
        return ""

    def to_dict(self) -> dict:
        self._show_message()
        return {}

    def query(self, datapath: DataPath) -> list:
        self._show_message()
        return []

    def get_paths(self) -> t.List[DataPath]:
        self._show_message()
        return []


# Static or singleton NULL_PARSER
NULL_PARSER = NullParser()
