from __future__ import annotations

import typing as t
from abc import abstractmethod

from loguru import logger

from cfgparser.path.path import DataPath
from cfgparser.tree.finder import Query
from cfgparser.tree.transformer import Transformer


class AbstractParser:
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


class NullParser(AbstractParser):
    @staticmethod
    def _show_message() -> None:
        logger.info(
            "This is null parser and cannot parse and other operation, you need to use correct parser"
        )

    @staticmethod
    def identify(lines: t.Iterable) -> bool:
        return False

    def parse(self, lines: t.Iterable) -> None:
        self._show_message()

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


class BaseParser(NullParser):
    def __init__(self) -> None:
        self._tree: t.Any = None

    def dumps(self) -> str:
        if not self._tree:
            return ""
        return Query(self._tree.tokens).dump_str()

    def to_dict(self) -> dict:
        if not self._tree:
            return {}

        return Query(self._tree.tokens).to_dict()

    def query(self, datapath: DataPath) -> list:
        if not self._tree:
            return []

        tokens = Query(self._tree.tokens).query(datapath)
        return [Transformer(t).to_dict() for t in tokens]

    def get_paths(self) -> t.List[DataPath]:
        if not self._tree:
            return []

        return Query(self._tree.tokens).get_paths()


# Static or singleton NULL_PARSER
NULL_PARSER = NullParser()
