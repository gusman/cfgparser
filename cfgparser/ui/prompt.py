from __future__ import annotations

import argparse
import io
import json
import typing as t

from prompt_toolkit import PromptSession
from prompt_toolkit import print_formatted_text as prompt_print
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.completion import CompleteEvent
from prompt_toolkit.completion import Completer
from prompt_toolkit.completion import Completion
from prompt_toolkit.document import Document

from cfgparser.base import base
from cfgparser.cisco.parser import Parser as CiscoParser
from cfgparser.nokia.classic.parser import Parser as NokiaClassicParser
from cfgparser.path.parser import Parser as DataPathParser
from cfgparser.path.path import DataPath


class CommandCompleter(Completer):
    def __init__(self):
        self.commands = ["parse", "path"]
        self.args = {
            "parse": {},
            "path": {},
        }

    def load_paths(self, datapaths: t.List[DataPath]) -> None:
        pass

    def _path_completion(self, path_parts: list) -> t.Iterable:
        def recurse_path_tree(path_tree: dict, path_parts: list):
            ret: t.List[t.Tuple[str, str]] = []
            if not path_parts:
                return ret

            search_text = path_parts[0]
            if len(path_parts) == 1:
                for k, v in path_tree.items():
                    if k == search_text and isinstance(v, dict):
                        ret.extend([(k, "") for k in v])

                    elif k.startswith(search_text):
                        ret.append((k, search_text))
            else:
                for k, v in path_tree.items():
                    if k.startswith(search_text) and isinstance(v, dict):
                        result = recurse_path_tree(v, path_parts[1:])
                        if result:
                            ret.extend(result)

            return ret

        path_tree = self.args["path"]
        if path_parts:
            founds = recurse_path_tree(path_tree, path_parts)
        else:
            founds = [(k, "") for k in path_tree]

        for found, search_text in founds:
            if " " in found or "/" in found:
                found = f'"{found}"'

            yield found, search_text

    # Need refactore and clean up
    def get_completions(
        self, document: Document, complete_event: CompleteEvent
    ) -> t.Iterable[Completion]:

        line_parts = document.current_line_before_cursor.split(" ", 1)
        cmd = line_parts[0]

        if len(line_parts) <= 1:
            for c in self.commands:
                if c.startswith(cmd):
                    yield Completion(c, start_position=-len(cmd))

        elif cmd == "path" and len(line_parts) >= 2:
            path_text = line_parts[1]
            datapath = DataPathParser(path_text).parse(clean_text=False)

            for path, search_text in self._path_completion(datapath.paths):

                offset = 0
                if len(search_text) == 0 and path_text:
                    # Count string limiter and string markers
                    for s in reversed(path_text):
                        if s == '"':
                            offset += 1
                        elif s == "/":
                            offset += 1
                            break
                        else:
                            offset = 0
                            break
                    path = f"/{path}"

                elif search_text:
                    path_text = path_text.rstrip(search_text)

                    for s in reversed(path_text):
                        if s == '"':
                            offset += 1
                        elif s == "/":
                            break
                        else:
                            offset = 0
                            break

                yield Completion(path, start_position=-(len(search_text) + offset))


class CommandLine:
    def __init__(self, completer: CommandCompleter):
        self._cmd_parse = argparse.ArgumentParser(prog="parse", exit_on_error=False)
        self._cmd_parse.add_argument("configfile", help="Path of config file to parse")

        self._cmd_path = argparse.ArgumentParser(prog="path", exit_on_error=False)
        self._cmd_path.add_argument("datapath", help="Data path to retrieve")

        self._exit_cmds = ["quit"]

        self._cmd_arg_parsers = {"parse": self._cmd_parse, "path": self._cmd_path}
        self._cmd_handlers = {
            "parse": self._handle_cmd_parse,
            "path": self._handle_cmd_path,
        }

        # Need to refactor
        self._parser_list: t.List[base.BaseParser] = [
            NokiaClassicParser(),
            CiscoParser(),
        ]
        self._parser = base.NULL_PARSER
        self._completer = completer

    def _identify_parser(self, fd: io.TextIOBase) -> base.BaseParser | None:
        parser = None
        for p in self._parser_list:
            prompt_print(f"Checking parser: {p}")
            fd.seek(0)
            if p.identify(fd):
                parser = p
                break

        fd.seek(0)
        return parser

    def _handle_cmd_parse(self, args) -> None:
        cfgfile = args.configfile

        prompt_print(f"Trying to parse '{cfgfile}'")
        try:
            with open(args.configfile) as f_cfg:
                parser = self._identify_parser(f_cfg)
                if parser:
                    self._parser = parser
                    self._parser.parse(f_cfg)
                else:
                    prompt_print("Cannot find correct parser")
        except OSError:
            prompt_print.warning(f"Cannot open file '{cfgfile}'")
        else:
            prompt_print(f"Sucess parse file '{cfgfile}'")

            self._completer.args["path"] = self._parser.to_dict()

    def _handle_cmd_path(self, args) -> None:
        data_path = DataPathParser(args.datapath).parse()

        data = self._parser.query(data_path)
        prompt_print(json.dumps(data, indent=4))

    def parse_prompt_line(self, line: str) -> None:
        # Separate command and parameters
        words = line.split(" ", 1)

        # If empty do nothing
        if not words:
            return None

        # Quit command
        cmd = words[0]
        if words[0].lower() in self._exit_cmds:
            raise SystemExit

        # Command that requires parser
        args_parser = self._cmd_arg_parsers.get(cmd)
        if not args_parser:
            prompt_print(f"Command '{cmd}' is unknown or not recognized")
            return None

        # Need to handle this ..
        args = []
        if len(words) > 1:
            args = words[1:]

        try:
            result = args_parser.parse_args(args)
        except SystemExit as e:
            # Hack the message display
            msgs = repr(e)
            msgs = "\n".join(s for s in msgs.split("\n") if "SystemExit" not in s)
        else:
            cmd_handler = self._cmd_handlers.get(cmd)
            if cmd_handler:
                cmd_handler(result)

        return None


def start():
    completer = CommandCompleter()
    cmd_line = CommandLine(completer)
    session = PromptSession(
        completer=completer,
        complete_in_thread=True,
        auto_suggest=AutoSuggestFromHistory(),
    )

    while True:
        try:
            text = session.prompt("cfgparser >> ")
        except KeyboardInterrupt:
            continue
        except (EOFError, SystemExit):
            break
        else:
            cmd_line.parse_prompt_line(text)
