import argparse
import json
import typing as t

from loguru import logger

from cfgparser.base import base
from cfgparser.cisco.parser import CiscoParser
from cfgparser.nokia.classic.parser import NokiaClassicParser
from cfgparser.path.parser import DataPathParser
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
        "--datapath", type=str, help="the path of data in mode", required=False
    )

    # Parse sub command
    sub_parser.add_parser("prompt", help="enter cfgparse prompt ui")

    args = parser.parse_args()
    return args


def _parse(f_path: str, path: str) -> None:
    parsers: t.Dict[str, base.BaseParser] = {
        "Nokia Classic": NokiaClassicParser(),
        "Cisco": CiscoParser(),
    }

    parser = None
    with open(f_path, "r") as fd:
        for name, p in parsers.items():
            fd.seek(0)
            if p.identify(fd):
                logger.info(f"Check parser '{name}': compatible")
                parser = p
                break

            logger.info(f"Check parser '{name}': not compatible")

    if not parser:
        logger.info("Could not find correct parser")
        return None

    with open(f_path, "r") as fd:
        parser.parse(fd)

    if path:
        datapath = DataPathParser(path).parse()
        logger.info(
            f"Data:\n{json.dumps(parser.query(datapath), indent=4, sort_keys=True)}"
        )
    else:
        logger.info(f"Data:\n{json.dumps(parser.to_dict(), indent=4, sort_keys=True)}")

    return None


def run():
    args = _get_args()

    if args.command == "parse":
        _parse(args.config_file, args.datapath)

    elif args.command == "prompt":
        prompt.start()
