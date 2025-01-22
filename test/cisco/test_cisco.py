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
                "group ": {
                    "1 ": {"monitor": {"member": {"ip": "10.147.47.1"}}},
                    "2": {"monitor": {"peer": "bfd"}},
                }
            },
        },
        "bridge-domain ": {"10": "", "11": ""},
    }
    lines = cfg_text.split("\n")

    parser = cisco_parser.Parser()
    parser.parse(lines)
    result = parser.to_dict()
    assert ref == result
