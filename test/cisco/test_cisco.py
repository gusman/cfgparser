from cfgparser.cisco import parser as cisco_parser


def test_parser():
    cfg_text = """
username emergency privilege 15 secret 5 $1$ObpT$52dVW4rjMXDTHX/vKonFc.
!
redundancy
 mode sso
 interchassis group 1
  monitor
   member ip 10.147.47.1
 interchassis group 2
  monitor peer bfd

redundancy mode
redundancy interchassis group
bridge-domain 10 
bridge-domain 11 
"""

    ref = {
        "username": {
            "emergency": {
                "privilege": {"15": {"secret": {"5": "$1$ObpT$52dVW4rjMXDTHX/vKonFc."}}}
            }
        },
        "redundancy": {
            "mode": "sso",
            "interchassis": {
                "group": {
                    "1": {"monitor": {"member": {"ip": "10.147.47.1"}}},
                    "2": {"monitor": {"peer": "bfd"}},
                }
            },
        },
        "bridge-domain": {"10": "", "11": ""},
    }
    lines = cfg_text.split("\n")

    parser = cisco_parser.Parser()
    parser.parse(lines)
    result = parser.to_dict()
    assert ref == result


def test_parse_isis():
    cfg_text = """
router isis ADI
 net 49.0010.0101.4704.7128.00
 is-type level-2-only
 metric-style wide
 set-overload-bit on-startup 360
 max-lsp-lifetime 65535
 lsp-refresh-interval 65000
 spf-interval 5 1 50
 prc-interval 5 1 50
 lsp-gen-interval 5 1 50
 nsf ietf
 nsf interface wait 60
 fast-reroute per-prefix level-2 all
 fast-reroute remote-lfa level-2 mpls-ldp
 maximum-paths 1
 bfd all-interfaces
 mpls ldp sync
!
"""

    ref = {
        "router": {
            "isis": {
                "ADI": {
                    "net": "49.0010.0101.4704.7128.00",
                    "is-type": "level-2-only",
                    "metric-style": "wide",
                    "set-overload-bit": {"on-startup": "360"},
                    "max-lsp-lifetime": "65535",
                    "lsp-refresh-interval": "65000",
                    "spf-interval": {"5": {"1": "50"}},
                    "prc-interval": {"5": {"1": "50"}},
                    "lsp-gen-interval": {"5": {"1": "50"}},
                    "nsf ietf": {"interface": {"wait": "60"}},
                    "fast-reroute": {
                        "per-prefix": {"level-2": "all"},
                        "remote-lfa": {"level-2": "mpls-ldp"},
                    },
                    "maximum-paths": "1",
                    "bfd": "all-interfaces",
                    "mpls": {"ldp": "sync"},
                }
            }
        }
    }
    lines = cfg_text.split("\n")

    parser = cisco_parser.Parser()
    parser.parse(lines)
    result = parser.to_dict()

    assert ref == result
