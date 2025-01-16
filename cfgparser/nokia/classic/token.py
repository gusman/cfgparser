from __future__ import annotations

import typing as t
from abc import ABC
from abc import abstractmethod

INDENT_SZ = 4


class Token:
    def __init__(
        self,
        name: str,
        value: t.Optional[str],
        indent: int,
        params: t.Optional[t.List] = None,
        childs: t.Optional[t.Dict] = None,
    ):
        self.name: str = name
        self.value: t.Optional[str] = value
        self.indent: int = indent
        self.params: list = []
        self.childs: dict = {}

        if params:
            self.params = params

        if childs:
            self.childs = childs

    @property
    def id(self):
        if isinstance(self.value, str):
            return f"{self.name} {self.value}"
        else:
            return self.name

    def is_attr_same(self, token: Token) -> bool:
        return (
            (self.name == token.name)
            and (self.indent == token.indent)
            and (self.value == token.value)
        )

    def find_token(self, token: Token) -> None | Token:
        def recurse_find(token_tree: Token, token: Token) -> None | Token:
            if token_tree.is_attr_same(token):
                return token_tree

            for c in token_tree.childs.values():
                ret = recurse_find(c, token)
                if ret:
                    return ret
            return None

        return recurse_find(self, token)


class AbstractTokenBuilder(ABC):
    @abstractmethod
    def check_rule(self, words: t.List[str]) -> bool: ...

    @abstractmethod
    def create(self, words: t.List[str], indent: int) -> Token: ...


class DefaultTokenBuilder(AbstractTokenBuilder):
    @staticmethod
    def check_rule(words: list) -> bool:
        return True

    @staticmethod
    def create(words: list, indent: int) -> Token:
        name = words[0]
        value = None
        params = []

        if len(words) > 1:
            value = words[1]

            if name == "no":
                name, value = value, name

        if len(words) > 2:
            params = words[2:]

        return Token(name, value, indent, params)


class ShutdownTokenBuilder(AbstractTokenBuilder):
    @staticmethod
    def check_rule(words: list) -> bool:
        if len(words) == 1 and words[0] == "shutdown":
            return True

        if len(words) == 2 and words[0] == "no" and words[1] == "shutdown":
            return True

        return False

    @staticmethod
    def create(words: list, indent: int) -> Token:
        if len(words) == 1:
            name = "shutdown"
            value = "yes"
        else:
            name = "shutdown"
            value = "no"

        return Token(name, value, indent)


class BfdTokenBuilder(AbstractTokenBuilder):
    @staticmethod
    def check_rule(words: list) -> bool:
        if len(words) < 7:
            return False

        if all(
            (
                words[0] == "bfd",
                "receive" in words,
                "multiplier" in words,
                "type" in words,
            )
        ):
            return True

        return False

    @staticmethod
    def create(words: list, indent: int) -> Token:
        name, tx_val, __, rx_val, __, multi_val, __, type_val = words

        token = Token(name, None, indent)

        child_indent = indent + INDENT_SZ
        token.childs["transmit"] = Token("transmit", rx_val, child_indent)
        token.childs["rx_token"] = Token("receive", tx_val, child_indent)
        token.childs["multi"] = Token("multi", multi_val, child_indent)
        token.childs["type"] = Token("type", type_val, child_indent)

        return token


class SdpTokenBuilder(AbstractTokenBuilder):
    @staticmethod
    def check_rule(words: list) -> bool:
        if len(words) < 4:
            return False

        if all(
            (
                words[0] == "sdp",
                words[3] == "create",
            )
        ):
            return True

        return False

    @staticmethod
    def create(words: list, indent: int) -> Token:
        name, value, delivery_type, __ = words
        token = Token(name, value, indent)

        child_indent = indent + INDENT_SZ
        token.childs["delivery-type"] = Token(
            "delivery-type", delivery_type, child_indent
        )

        return token


class SvcCustomerTokenBuilder(AbstractTokenBuilder):
    @staticmethod
    def check_rule(words: list) -> bool:
        if len(words) < 5:
            return False

        if all(
            (
                words[0] == "customer",
                words[2] == "name",
                words[4] == "create",
            )
        ):
            return True

        return False

    @staticmethod
    def create(words: list, indent: int) -> Token:
        name, value, __, cust_name, __ = words
        token = Token(name, value, indent)

        child_indent = indent + INDENT_SZ
        token.childs["name"] = Token("name", cust_name, child_indent)

        return token


class VplsTokenBuilder(AbstractTokenBuilder):
    @staticmethod
    def check_rule(words: list) -> bool:
        if len(words) < 7:
            return False

        if all(
            (
                words[0] == "vpls",
                words[2] == "name",
                words[4] == "customer",
                words[6] == "create",
            )
        ):
            return True

        return False

    @staticmethod
    def create(words: list, indent: int) -> Token:
        name, value, __, vpls_name, __, cust_id, __ = words
        token = Token(name, value, indent)

        child_indent = indent + INDENT_SZ
        token.childs["name"] = Token("name", vpls_name, child_indent)
        token.childs["customer"] = Token("customer", cust_id, child_indent)

        return token


class EpipeTokenBuilder(AbstractTokenBuilder):
    @staticmethod
    def check_rule(words: list) -> bool:
        if len(words) < 7:
            return False

        if all(
            (
                words[0] == "epipe",
                words[2] == "name",
                words[4] == "customer",
                words[6] == "create",
            )
        ):
            return True

        return False

    @staticmethod
    def create(words: list, indent: int) -> Token:
        name, value, __, epipe_name, __, cust_id, __ = words
        token = Token(name, value, indent)

        child_indent = indent + INDENT_SZ
        token.childs["name"] = Token("name", epipe_name, child_indent)
        token.childs["customer"] = Token("customer", cust_id, child_indent)

        return token


class TokenBuilder:
    __LIST_OF_BUILDER: t.List[AbstractTokenBuilder] = [
        ShutdownTokenBuilder(),
        BfdTokenBuilder(),
        SdpTokenBuilder(),
        SvcCustomerTokenBuilder(),
        VplsTokenBuilder(),
        EpipeTokenBuilder(),
    ]

    @staticmethod
    def create_token(words: list, indent: int) -> Token:
        for builder in TokenBuilder.__LIST_OF_BUILDER:
            if builder.check_rule(words):
                return builder.create(words, indent)

        return DefaultTokenBuilder.create(words, indent)
