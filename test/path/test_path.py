from cfgparser.path.parser import DataPathParser


def test_path_parser():
    text = '/configure/router "management 1"/ctx'
    ref = ["configure", "router management 1", "ctx"]
    path = DataPathParser(text).parse()
    assert ref == path.paths

    text = '/configure/password "$2y$10$TQrZlpBDra86.qoexZUzQeBXDY1FcdDhGWdD9lLxMuFyPVSm0OGy6"'
    ref = [
        "configure",
        "password $2y$10$TQrZlpBDra86.qoexZUzQeBXDY1FcdDhGWdD9lLxMuFyPVSm0OGy6",
    ]
    path = DataPathParser(text).parse()
    assert ref == path.paths
