from __future__ import annotations

import copy
import typing as t

from cfgparser.path.path import DataPath
from cfgparser.tree.token import Token
from cfgparser.tree.transformer import Transformer


class Finder:
    def __init__(self, token: Token) -> None:
        self.token = token

    @staticmethod
    def _is_attr_same(token_tree: Token, token: Token) -> bool:
        return (
            (token_tree.name == token.name)
            and (token_tree.indent == token.indent)
            and (token_tree.value == token.value)
        )

    def _recurse_find(
        self, token_tree: Token, param: t.Any, f_compare: t.Callable
    ) -> None | Token:
        if f_compare(token_tree, param):
            return token_tree

        for c in token_tree.childs.values():
            ret = self._recurse_find(c, param, f_compare)
            if ret:
                return ret
        return None

    def _find_childs(
        self,
        token_tree: Token,
        param: t.Any,
        f_compare: t.Callable,
    ) -> t.List[Token]:
        return [c for c in token_tree.childs.values() if f_compare(c, param)]

    def is_attr_same(self, token: Token) -> bool:
        return self._is_attr_same(self.token, token)

    def find_token(self, token: Token) -> None | Token:
        return self._recurse_find(self.token, token, self._is_attr_same)

    def find_childs_by_id(self, token_id: str) -> t.List[Token]:
        def _compare(token_tree: Token, param: str) -> bool:
            return token_tree.id.lower().startswith(param.lower())

        return self._find_childs(self.token, token_id, _compare)

    @staticmethod
    def recurse_merge_token(token_dst: Token, token_src: Token) -> bool:
        ret = False
        if not Finder(token_dst).is_attr_same(token_src):
            return ret

        if not token_src.childs:
            return ret

        ret = True
        for token_id, src_val in token_src.childs.items():
            if token_id not in token_dst.childs:
                token_dst.childs[token_id] = src_val
            else:
                dst_val = token_dst.childs[token_id]

                if not isinstance(dst_val, Token) and isinstance(src_val, Token):
                    token_dst.childs[token_id] = src_val
                elif (
                    isinstance(dst_val, Token)
                    and not dst_val.childs
                    and isinstance(src_val, Token)
                    and src_val.childs
                ):
                    token_dst.childs[token_id] = src_val
                elif (
                    isinstance(dst_val, Token)
                    and dst_val.childs
                    and isinstance(src_val, Token)
                    and src_val.childs
                ):
                    if Finder.recurse_merge_token(dst_val, src_val):
                        ret = True
                else:
                    pass

        return ret


class Query:
    def __init__(self, tokens: t.List[Token]) -> None:
        self.tokens: t.List[Token] = tokens

    def dump_str(self) -> str:
        ret = ""
        for idx, root_token in enumerate(self.tokens):
            print(idx, root_token)
            ret += f"[root: {idx}]\n"
            ret += Transformer(root_token).to_structured_text()
            ret += "\n"

        return ret

    def to_dict(self) -> dict:
        lst = []

        for root_token in self.tokens:
            lst.append(Transformer(root_token).to_dict())

        ret = {}
        for data in lst:
            if isinstance(data, dict):
                ret.update(data)

        return ret

    def query(self, datapath: DataPath) -> list:
        tokens_to_search = self.tokens
        tokens_to_store: t.List[Token] = []
        paths = datapath.paths

        # Find roots
        roots = []
        path = paths.pop(0)
        for token in self.tokens:
            if token.id.lower().startswith(path.lower()):
                roots.append(token)

        # Query path on each token childs
        for p in paths:
            tokens_to_store = []

            for token in tokens_to_search:
                founds = Finder(token).find_childs_by_id(p)
                if founds:
                    tokens_to_store += founds

            # Setup searched tokens for next path
            tokens_to_search = tokens_to_store

        if not paths:
            ret = roots
        else:
            ret = tokens_to_store

        return ret

    def get_paths(self) -> t.List[DataPath]:

        def traverse_data(token: Token, datapath: DataPath) -> t.List[DataPath]:
            datapath.add(token.id)
            paths = [copy.deepcopy(datapath)]

            if token.childs:
                for c in token.childs.values():
                    ret = traverse_data(c, copy.deepcopy(datapath))
                    paths.extend(ret)

            return paths

        # Create list of list data_path
        paths = []
        for token in self.tokens:
            datapath = DataPath()
            paths.extend(traverse_data(token, datapath))

        return paths
