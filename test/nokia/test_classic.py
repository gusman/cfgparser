from cfgparser.nokia.classic import parser as nc_parser


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
configure
    system
        netconf
            listen
                no shutdown
            no auto-config-save
        management-interface
            cli
                md-cli
                    no auto-config-save
        config-backup 5
        location "site 1"
        name "PE1"
"""

    ref = [line.rstrip() for line in ref.split("\n") if line.strip()]
    ref = "\n".join(ref)

    lines = cfg_text.split("\n")

    parser = nc_parser.Parser()
    parser.parse(lines)

    result = parser.dumps()

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

    ref = [line.rstrip() for line in ref.split("\n") if line.strip()]
    ref = "\n".join(ref)

    lines = cfg_text.split("\n")

    parser = nc_parser.Parser()
    parser.parse(lines)

    result = parser.dumps()

    assert ref == result
