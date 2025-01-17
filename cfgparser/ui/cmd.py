import argparse
import json

from cfgparser.nokia.classic import parser as nc_parser
from cfgparser.path import parser as dp_parser
from cfgparser.ui import prompt


def _get_args():
    parser = argparse.ArgumentParser(prog="cfgparser")
    sub_parser = parser.add_subparsers(
        dest="command", help="commands of cfgparser", required=True
    )

    # Parse sub command
    cmd_parse = sub_parser.add_parser("parse", help="parse a config file")
    cmd_parse.add_argument("config_file", type=str, help="config file to parse")
    cmd_parse.add_argument(
        "--data-path", type=str, help="the path of data in mode", required=False
    )

    # Parse sub command
    sub_parser.add_parser("prompt", help="enter cfgparse prompt ui")

    args = parser.parse_args()
    return args


def _parse_nokia_classic(f_path: str, path: str) -> None:
    parser = nc_parser.Parser()
    with open(f_path, "r") as fd:
        parser.parse(fd)

    if path:
        datapath = dp_parser.Parser(path).parse()
        print(json.dumps(parser.query(datapath), indent=4, sort_keys=True))
    else:
        print(json.dumps(parser.to_dict(), indent=4, sort_keys=True))


def run():
    args = _get_args()

    if args.command == "parse":
        _parse_nokia_classic(args.config_file, args.path)
    elif args.command == "prompt":
        prompt.start()
