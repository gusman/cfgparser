from __future__ import annotations

from cfgparser.nokia.classic.token import Token


class Transformer:
    def __init__(self, token: Token) -> None:
        self.token = token

    def to_structured_text(self) -> str:
        def enclose_string(text: str) -> str:
            if " " in text:
                text = f'"{text}"'
            return text

        def traverse_text(token: Token):
            indent = ""
            for __ in range(0, token.indent):
                indent += " "

            text = indent + enclose_string(token.name)
            if token.value:
                text += " " + enclose_string(token.value)

            if token.params:
                text = f"{text} {" ".join([enclose_string(t) for t in token.params])}"

            for c in token.childs.values():
                text += "\n"
                text += traverse_text(c)

            return text

        return traverse_text(self.token)

    def to_dict(self) -> dict:
        data: dict = {}

        def traverse_data(token: Token, data: dict):
            if token.is_container or token.childs:
                data[token.id] = {}
                for c in token.childs.values():
                    traverse_data(c, data[token.id])
            else:
                if token.params:
                    data[token.name] = [token.value] + token.params
                elif token.value:
                    data[token.name] = token.value
                else:
                    data[token.name] = ""

        traverse_data(self.token, data)
        return data
