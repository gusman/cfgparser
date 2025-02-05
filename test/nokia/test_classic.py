from cfgparser.nokia.classic.parser import NokiaClassicParser
from cfgparser.nokia.classic.parser import NokiaTree
from cfgparser.path.parser import DataPathParser


def test_parser_pass():
    cfg_text = """
exit all
configure
#--------------------------------------------------
echo "System Configuration"
#--------------------------------------------------
    system
        name "PE1"
        location "site 1"
        config-backup 5
        management-interface
            cli
                md-cli
                    no auto-config-save
                exit
            exit
        exit
        netconf
            no auto-config-save
            listen
                no shutdown
            exit
        exit
    exit
exit all
"""

    ref = """
[root: 0]
configure
    system
        netconf
            listen
                shutdown no
            auto-config-save no
        management-interface
            cli
                md-cli
                    auto-config-save no
        config-backup 5
        location "site 1"
        name PE1
"""

    ref = [line.rstrip() for line in ref.split("\n") if line.strip()]
    ref = "\n".join(ref)

    lines = cfg_text.split("\n")

    parser = NokiaClassicParser()
    parser.parse(lines)

    result = parser.dumps()
    parts = [line.rstrip() for line in result.split("\n") if line.strip()]
    result = "\n".join(parts)

    assert ref == result


def test_parser_merge_container():
    cfg_text = """
exit all
configure
#--------------------------------------------------
echo "System Configuration"
#--------------------------------------------------
    system
        field
        field 10
        container
            field
            field 2
        exit
        id_container 10
            x1_field
            x2_field 10
        exit
        field 11
    exit
    system
        field 20
        field 21
        container
            inner_field
        exit
        id_container 10
            y1_field
            y2_field 11
        exit
        id_container 20
            y1_field
            y2_field 11
        exit

    exit
exit all
"""

    ref = """
[root: 0]
configure
    system
        id_container 20
            y2_field 11
            y1_field
        id_container 10
            y2_field 11
            y1_field
            x2_field 10
            x1_field
        container
            inner_field
            field 2
            field
        field 21
        field 20
        field 11
        field 10
        field
"""

    parts = [line.rstrip() for line in ref.split("\n") if line.strip()]
    ref = "\n".join(parts)

    lines = cfg_text.split("\n")

    parser = NokiaClassicParser()
    parser.parse(lines)

    result = parser.dumps()
    parts = [line.rstrip() for line in result.split("\n") if line.strip()]
    result = "\n".join(parts)

    assert ref == result


def test_to_dict():
    cfg_text = """
exit all
configure
#--------------------------------------------------
echo "System Configuration"
#--------------------------------------------------
    system
        name "PE1"
        location "site 1"
        config-backup 5
        management-interface
            cli
                md-cli
                    no auto-config-save
                exit
            exit
        exit
        netconf
            no auto-config-save
            listen
                no shutdown
            exit
        exit
    exit
        card 1
            card-type iom-1
            mda 1
                mda-type me6-100gb-qsfp28
                no shutdown
            exit
            mda 2
                mda-type me6-100gb-qsfp28
                no shutdown
            exit
            no shutdown
        exit
    exit
#--------------------------------------------------
echo "Connector Configuration"
#--------------------------------------------------
    port 1/1/c1
        connector
            breakout c1-100g
        exit
        no shutdown
    exit
    port 1/1/c2
        connector
            breakout c1-100g
        exit
        no shutdown
    exit
exit all
"""

    ref = {
        "configure": {
            "port 1/1/c2": {"shutdown": "no", "connector": {"breakout": "c1-100g"}},
            "port 1/1/c1": {"shutdown": "no", "connector": {"breakout": "c1-100g"}},
            "system": {
                "netconf": {"listen": {"shutdown": "no"}, "auto-config-save": "no"},
                "management-interface": {"cli": {"md-cli": {"auto-config-save": "no"}}},
                "config-backup": "5",
                "location": "site 1",
                "name": "PE1",
                "card 1": {
                    "shutdown": "no",
                    "mda 2": {"shutdown": "no", "mda-type": "me6-100gb-qsfp28"},
                    "mda 1": {"shutdown": "no", "mda-type": "me6-100gb-qsfp28"},
                    "card-type": "iom-1",
                },
            },
        }
    }

    lines = cfg_text.split("\n")

    parser = NokiaClassicParser()
    parser.parse(lines)

    result = parser.to_dict()
    assert result == ref


def test_tokenize_line():
    line = ' mda "iom high:375" up "hero here" 1\n'

    result = NokiaTree._tokenize_line(line)
    assert result == ["mda", "iom high:375", "up", "hero here", "1"]

    line = ' mda "hello \n'
    result = NokiaTree._tokenize_line(line)
    assert result == ["mda", '"hello']

    line = ' mda hello "\n'
    result = NokiaTree._tokenize_line(line)
    assert result == ["mda", "hello", '"']

    line = ' "mda hello "\n'
    result = NokiaTree._tokenize_line(line)
    assert result == ["mda hello "]

    line = ' "mda hello \n'
    result = NokiaTree._tokenize_line(line)
    assert result == ['"mda', "hello"]

    line = ' user "snmpv3_user" \n'
    result = NokiaTree._tokenize_line(line)
    assert result == ["user", "snmpv3_user"]


def test_multiple_params():
    cfg_text = """
configure
    router Base
        interface "system"
            address 1.1.1.5/32
            no shutdown
        exit
        interface "to_p1_100g_1"
            address 10.10.10.10/30
            ldp-sync-timer 10
            port 1/1/1
            ingress
            exit
            bfd 10 receive 10 multiplier 3 type fp
            no shutdown
        exit
        autonomous-system 65001
        router-id 1.1.1.5
    exit
exit
"""

    ref = {
        "configure": {
            "router Base": {
                "router-id": "1.1.1.5",
                "autonomous-system": "65001",
                "interface to_p1_100g_1": {
                    "shutdown": "no",
                    "bfd": {
                        "multi": "3",
                        "receive": "10",
                        "transmit": "10",
                        "type": "fp",
                    },
                    "ingress": {},
                    "port": "1/1/1",
                    "ldp-sync-timer": "10",
                    "address": "10.10.10.10/30",
                },
                "interface system": {"shutdown": "no", "address": "1.1.1.5/32"},
            }
        }
    }

    lines = cfg_text.split("\n")

    parser = NokiaClassicParser()
    parser.parse(lines)

    assert ref == parser.to_dict()


def test_multiple_parts_id():
    cfg_text = """
configure
    service
        sdp 560 mpls create
            far-end 1.1.1.6
            bgp-tunnel
            keep-alive
                shutdown
            exit
            no shutdown
        exit
        customer 1 name "1" create
            description "Default customer"
        exit
        customer 2 name "2" create
        exit
        vpls 100 name "100" customer 2 create
            stp
                shutdown
            exit
            sap 1/1/2:100 create
                no shutdown
            exit
            no shutdown
        exit
        epipe 560 name "560" customer 1 create
            sap 1/1/2:10 create
                no shutdown
            exit
            spoke-sdp 560:10 create
                no shutdown
            exit
            no shutdown
        exit
    exit
exit all
"""
    ref = {
        "configure": {
            "service": {
                "epipe 560": {
                    "name": "560",
                    "customer": "1",
                    "shutdown": "no",
                    "spoke-sdp 560:10": {"shutdown": "no"},
                    "sap 1/1/2:10": {"shutdown": "no"},
                },
                "vpls 100": {
                    "name": "100",
                    "customer": "2",
                    "shutdown": "no",
                    "sap 1/1/2:100": {"shutdown": "no"},
                    "stp": {"shutdown": "yes"},
                },
                "customer 2": {"name": "2"},
                "customer 1": {"name": "1", "description": "Default customer"},
                "sdp 560": {
                    "delivery-type": "mpls",
                    "shutdown": "no",
                    "keep-alive": {"shutdown": "yes"},
                    "bgp-tunnel": "",
                    "far-end": "1.1.1.6",
                },
            }
        }
    }
    lines = cfg_text.split("\n")

    parser = NokiaClassicParser()
    parser.parse(lines)

    result = parser.to_dict()
    assert ref == result


def test_get_paths():
    cfg_text = """
configure
    router Base
        interface "system"
            address 1.1.1.5/32
            no shutdown
        exit
        interface "to_p1_100g_1"
            address 10.10.10.10/30
            ldp-sync-timer 10
            port 1/1/1
            ingress
            exit
            bfd 10 receive 10 multiplier 3 type fp
            no shutdown
        exit
        autonomous-system 65001
        router-id 1.1.1.5
    exit
exit
"""
    lines = cfg_text.split("\n")

    parser = NokiaClassicParser()
    parser.parse(lines)
    data_paths = parser.get_paths()

    ref = [
        ["configure"],
        ["configure", "router Base"],
        ["configure", "router Base", "router-id 1.1.1.5"],
        ["configure", "router Base", "autonomous-system 65001"],
        ["configure", "router Base", "interface to_p1_100g_1"],
        ["configure", "router Base", "interface to_p1_100g_1", "shutdown no"],
        ["configure", "router Base", "interface to_p1_100g_1", "bfd"],
        ["configure", "router Base", "interface to_p1_100g_1", "bfd", "transmit 10"],
        ["configure", "router Base", "interface to_p1_100g_1", "bfd", "receive 10"],
        ["configure", "router Base", "interface to_p1_100g_1", "bfd", "multi 3"],
        ["configure", "router Base", "interface to_p1_100g_1", "bfd", "type fp"],
        ["configure", "router Base", "interface to_p1_100g_1", "ingress"],
        ["configure", "router Base", "interface to_p1_100g_1", "port 1/1/1"],
        ["configure", "router Base", "interface to_p1_100g_1", "ldp-sync-timer 10"],
        [
            "configure",
            "router Base",
            "interface to_p1_100g_1",
            "address 10.10.10.10/30",
        ],
        ["configure", "router Base", "interface system"],
        ["configure", "router Base", "interface system", "shutdown no"],
        ["configure", "router Base", "interface system", "address 1.1.1.5/32"],
    ]

    result = [p.paths for p in data_paths]
    assert result == ref


def test_query():
    cfg_text = """
configure
    router Base
        interface "system"
            address 1.1.1.5/32
            no shutdown
        exit
        interface "to_p1_100g_1"
            address 10.10.10.10/30
            ldp-sync-timer 10
            port 1/1/1
            ingress
            exit
            bfd 10 receive 10 multiplier 3 type fp
            no shutdown
        exit
        autonomous-system 65001
        router-id 1.1.1.5
    exit
exit
"""
    lines = cfg_text.split("\n")

    cfg_parser = NokiaClassicParser()
    cfg_parser.parse(lines)

    datapath = DataPathParser("/configure/router/interface").parse()
    result = cfg_parser.query(datapath)

    ref = [
        {
            "interface to_p1_100g_1": {
                "shutdown": "no",
                "bfd": {"transmit": "10", "receive": "10", "multi": "3", "type": "fp"},
                "ingress": {},
                "port": "1/1/1",
                "ldp-sync-timer": "10",
                "address": "10.10.10.10/30",
            }
        },
        {"interface system": {"shutdown": "no", "address": "1.1.1.5/32"}},
    ]

    assert ref == result
