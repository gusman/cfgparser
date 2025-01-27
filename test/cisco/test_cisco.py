from cfgparser.cisco.parser import CiscoParser


def test_parser():
    cfg_text = """
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

    parser = CiscoParser()
    parser.parse(lines)
    result = parser.to_dict()
    assert ref == result


def test_parse_banner():
    cfg_text = """
!
!
!
control-plane
!
banner login ^CCCCCCCC
####################################################################################
You are about to log on to a proprietary computer system where access
is provided, by the Owner of the computer system, only to authorised
users. If you are not authorised to use this system, please refrain
from doing so. All activities on this system are being monitored.
Unauthorized  access to this system may be subjected to legal action
and/or prosecution.
####################################################################################
^C
banner motd ^CC^C
!
line con 0
 session-timeout 10
 exec-timeout 5 0
 logging synchronous
 exec prompt timestamp
 transport output ssh
 stopbits 1
line aux 0
 stopbits 1
line vty 0 4
 session-timeout 60
 exec-timeout 60 0
 logging synchronous
 exec prompt timestamp
 transport input telnet ssh
 transport output telnet ssh
!
ntp source Loopback20
ntp server vrf OAM 10.144.80.129 prefer
ntp server vrf OAM 10.144.80.130
!
"""

    ref = {
        "control-plane": "",
        "banner": {
            "login": "^CCCCCCCC\n####################################################################################\nYou are about to log on to a proprietary computer system where access\nis provided, by the Owner of the computer system, only to authorised\nusers. If you are not authorised to use this system, please refrain\nfrom doing so. All activities on this system are being monitored.\nUnauthorized access to this system may be subjected to legal action\nand/or prosecution.\n####################################################################################\n^C",
            "motd": "^CC^C",
        },
        "line": {
            "con": {
                "0": {
                    "session-timeout": "10",
                    "exec-timeout": {"5": "0"},
                    "logging": "synchronous",
                    "exec": {"prompt": "timestamp"},
                    "transport": {"output": "ssh"},
                    "stopbits": "1",
                }
            },
            "aux": {"0": {"stopbits": "1"}},
            "vty": {
                "0": {
                    "4": {
                        "session-timeout": "60",
                        "exec-timeout": {"60": "0"},
                        "logging": "synchronous",
                        "exec": {"prompt": "timestamp"},
                        "transport": {
                            "input": {"telnet": "ssh"},
                            "output": {"telnet": "ssh"},
                        },
                    }
                }
            },
        },
        "ntp": {
            "source": "Loopback20",
            "server": {
                "vrf": {"OAM": {"10.144.80.129": "prefer", "10.144.80.130": ""}}
            },
        },
    }

    lines = cfg_text.split("\n")

    parser = CiscoParser()
    parser.parse(lines)

    result = parser.to_dict()
    assert result == ref


def test_parse_token_builder():
    cfg_text = """
username nsn password 7 12312312312312
username sudheer privilege 15 secret 5 a12384798987987cxvzxc9v87
username anil privilege 15 secret 5 $0982asdfasldfkjdli$
username sesha privilege 15 secret 5 $/askdjfieowka;lsdkfjaeiwokj
"""

    ref = {
        "username": {
            "nsn": {"password": {"type": "7", "value": "12312312312312"}},
            "sudheer": {
                "privilege": {
                    "type": "15",
                    "secret": {"type": "5", "value": "a12384798987987cxvzxc9v87"},
                }
            },
            "anil": {
                "privilege": {
                    "type": "15",
                    "secret": {"type": "5", "value": "$0982asdfasldfkjdli$"},
                }
            },
            "sesha": {
                "privilege": {
                    "type": "15",
                    "secret": {"type": "5", "value": "$/askdjfieowka;lsdkfjaeiwokj"},
                }
            },
        }
    }

    lines = cfg_text.split("\n")

    parser = CiscoParser()
    parser.parse(lines)

    result = parser.to_dict()
    assert result == ref


def test_no_line_parser():
    cfg_text = """
no platform punt-keepalive disable-kernel-core
platform bfd-debug-trace 1
platform xconnect load-balance-hash-algo mac-ip-instanceid
platform tcam-parity-error enable
platform tcam-threshold alarm-frequency 1
interface Port-channel3
 description ADI-ADI;APHYDADIPAR01;mc-BSC01 Module-0;L1;001000M;XXXXXXXXXXXXXXXXXXXX;Po3;Po3
 no ip address
 no ip redirects
 no ip unreachables
 no ip proxy-arp
 negotiation auto
 storm-control broadcast level 0.10
 storm-control multicast level 0.10
 service-policy input ACCESS_IN
 service instance 101 ethernet
  encapsulation dot1q 101
  rewrite ingress tag pop 1 symmetric
  bridge-domain 101
 !
!
"""
    ref = {
        "platform": {
            "punt-keepalive": {"disable-kernel-core": "no"},
            "bfd-debug-trace": "1",
            "xconnect": {"load-balance-hash-algo": "mac-ip-instanceid"},
            "tcam-parity-error": "enable",
            "tcam-threshold": {"alarm-frequency": "1"},
        },
        "interface": {
            "Port-channel3": {
                "description": "ADI-ADI;APHYDADIPAR01;mc-BSC01 Module-0;L1;001000M;XXXXXXXXXXXXXXXXXXXX;Po3;Po3",
                "ip": {
                    "address": "no",
                    "redirects": "no",
                    "unreachables": "no",
                    "proxy-arp": "no",
                },
                "negotiation": "auto",
                "storm-control": {
                    "broadcast": {"level": "0.10"},
                    "multicast": {"level": "0.10"},
                },
                "service-policy": {"input": "ACCESS_IN"},
                "service": {
                    "instance": {
                        "101": {
                            "ethernet": {
                                "encapsulation": {"dot1q": "101"},
                                "rewrite": {
                                    "ingress": {"tag": {"pop": {"1": "symmetric"}}}
                                },
                                "bridge-domain": "101",
                            }
                        }
                    }
                },
            }
        },
    }
    lines = cfg_text.split("\n")

    parser = CiscoParser()
    parser.parse(lines)
    result = parser.to_dict()

    assert ref == result
