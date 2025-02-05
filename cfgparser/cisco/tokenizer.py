from __future__ import annotations

import ipaddress
import typing as t

from cfgparser.tree.token import AbstractTokenBuilder
from cfgparser.tree.token import Token


class _Attr:
    indent_step_size: int = 1


_attr = _Attr()


def get_indent_step_sz() -> int:
    return _attr.indent_step_size


def set_indent_step_sz(indent_sz: int) -> None:
    _attr.indent_step_size = indent_sz


class BannerToken(AbstractTokenBuilder):
    @staticmethod
    def check_rule(words: list) -> bool:
        if len(words) >= 2 and words[0] == "banner" and words[1] in ["login", "motd"]:
            return True

        return False

    @staticmethod
    def create(words: list, indent: int) -> Token:
        banner_token = Token(words[0], None, indent)
        banner_token.is_container = True

        child_token = Token(words[1], None, indent + _attr.indent_step_size)
        banner_token.childs[words[1]] = child_token

        if len(words) > 2:
            child_token.value = " ".join(words[2:])

        return banner_token


class IfaceIpAddressToken(AbstractTokenBuilder):
    @staticmethod
    def check_rule(words: list) -> bool:
        if len(words) != 3:
            return False

        if words[0] != "address":
            return False

        try:
            ipaddress.ip_address(words[1])
        except ValueError:
            return False

        try:
            ipaddress.ip_address(words[2])
        except ValueError:
            return False

        return True

    @staticmethod
    def create(words: list, indent: int) -> Token:
        addr_text, ipval, ipmask = words

        passwd_token = Token(addr_text, None, indent)
        passwd_token.is_container = True

        ipaddr_token = Token("ipaddress", ipval, indent + _attr.indent_step_size)
        ipmask_token = Token("netmask", ipmask, indent + _attr.indent_step_size)
        passwd_token.childs["ipaddress"] = ipaddr_token
        passwd_token.childs["netmask"] = ipmask_token

        return passwd_token


class UserPasswordToken(AbstractTokenBuilder):
    @staticmethod
    def check_rule(words: list) -> bool:
        if len(words) == 3 and words[0] == "password" and str(words[1]).isdigit():
            return True

        return False

    @staticmethod
    def create(words: list, indent: int) -> Token:
        passwd_text, passwd_type, passwd_val = words

        passwd_token = Token(passwd_text, None, indent)
        passwd_token.is_container = True

        type_token = Token("type", passwd_type, indent + _attr.indent_step_size)
        value_token = Token("value", passwd_val, indent + _attr.indent_step_size)
        passwd_token.childs["type"] = type_token
        passwd_token.childs["value"] = value_token

        return passwd_token


class UserPrivilegeToken(AbstractTokenBuilder):
    @staticmethod
    def check_rule(words: list) -> bool:
        if len(words) == 5 and words[0] == "privilege" and words[2] == "secret":
            return True

        return False

    @staticmethod
    def create(words: list, indent: int) -> Token:
        priv_text, priv_type, secret_text, secret_type, secret_val = words
        priv_token = Token(priv_text, None, indent)
        priv_token.is_container = True

        priv_type_token = Token("type", priv_type, indent + _attr.indent_step_size)

        secret_token = Token(secret_text, None, indent + _attr.indent_step_size)
        secret_token.is_container = True

        secret_type_token = Token("type", secret_type, indent + (_attr.indent_step_size * 2))
        secret_value_token = Token(
            "value", secret_val, indent + (_attr.indent_step_size * 2)
        )
        secret_token.childs["type"] = secret_type_token
        secret_token.childs["value"] = secret_value_token

        priv_token.childs["type"] = priv_type_token
        priv_token.childs["secret"] = secret_token

        return priv_token


class DescriptionToken(AbstractTokenBuilder):
    @staticmethod
    def check_rule(words: list) -> bool:
        if len(words) >= 2 and words[0] == "description":
            return True

        return False

    @staticmethod
    def create(words: list, indent: int) -> Token:
        desc_token = Token("description", " ".join(words[1:]), indent)

        return desc_token


__LIST_OF_BUILDER: t.List[AbstractTokenBuilder] = [
    BannerToken(),
    UserPrivilegeToken(),
    UserPasswordToken(),
    IfaceIpAddressToken(),
    # Description must be the last for matching
    # Because the check rule is a bit greedy
    DescriptionToken(),
]


def create_token(words: list, indent: int) -> Token | None:
    for builder in __LIST_OF_BUILDER:
        if builder.check_rule(words):
            return builder.create(words, indent)

    return None

    return None
