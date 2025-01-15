import argparse

from cfgparser.nokia.classic import parser as nc_parser


def _get_args():
    parser = argparse.ArgumentParser()

    parser.add_argument("config_file", type=str, help="config file to parse")
    args = parser.parse_args()
    return args


def _parse_nokia_classic(f_path: str) -> None:
    with open(f_path, "r") as fd:
        nc_parser.parse(fd)


def run():
    args = _get_args()
    _parse_nokia_classic(args.config_file)
