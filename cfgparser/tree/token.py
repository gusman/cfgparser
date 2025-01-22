from __future__ import annotations

import typing as t
from abc import ABC
from abc import abstractmethod



class Token:
    def __init__(
        self,
        name: str,
        value: t.Optional[str],
        indent: int,
        params: t.Optional[t.List] = None,
        childs: t.Optional[t.Dict] = None,
    ) -> None:
        self.name: str = name
        self.value: t.Optional[str] = value
        self.indent: int = indent
        self.params: list = []
        self.childs: dict = {}
        self.is_container: bool = False

        if params:
            self.params = params

        if childs:
            self.childs = childs

    @property
    def id(self) -> str:
        if isinstance(self.value, str):
            return f"{self.name} {self.value}"
        return self.name


class AbstractTokenBuilder(ABC):
    @staticmethod
    @abstractmethod
    def check_rule(words: t.List[str]) -> bool: ...

    @staticmethod
    @abstractmethod
    def create(words: t.List[str], indent: int) -> Token: ...
