import argparse

from cfgparser.nokia.classic import parser as nc_parser


def _get_args():
    parser = argparse.ArgumentParser()

    parser.add_argument("config_file", type=str, help="config file to parse")
    args = parser.parse_args()
    return args


def _parse_nokia_classic(f_path: str) -> None:
    parser = nc_parser.Parser()
    with open(f_path, "r") as fd:
        parser.parse(fd)
    print(parser.dumps())


def run():
    args = _get_args()
    _parse_nokia_classic(args.config_file)
