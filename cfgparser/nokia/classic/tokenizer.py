from __future__ import annotations

import typing as t

from cfgparser.tree.token import AbstractTokenBuilder
from cfgparser.tree.token import Token

INDENT_SZ = 4


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
        token.is_container = True

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
        token.is_container = True

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
        token.is_container = True

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
        token.is_container = True

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
        token.is_container = True

        child_indent = indent + INDENT_SZ
        token.childs["name"] = Token("name", epipe_name, child_indent)
        token.childs["customer"] = Token("customer", cust_id, child_indent)

        return token


__LIST_OF_BUILDER: t.List[AbstractTokenBuilder] = [
    ShutdownTokenBuilder(),
    BfdTokenBuilder(),
    SdpTokenBuilder(),
    SvcCustomerTokenBuilder(),
    VplsTokenBuilder(),
    EpipeTokenBuilder(),
]


def create_token(words: list, indent: int) -> Token:
    for builder in __LIST_OF_BUILDER:
        if builder.check_rule(words):
            return builder.create(words, indent)

    return DefaultTokenBuilder.create(words, indent)
