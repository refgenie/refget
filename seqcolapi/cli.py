from ubiquerg import VersionInHelpParser

from .const import PKG_NAME, seqcolapi_version


def build_parser():
    """
    Build argument parser

    :return argparse.ArgumentParser
    """
    banner = "%(prog)s - API for sequence collections"
    additional_description = (
        "For subcommand-specific options, type: '%(prog)s <subcommand> -h'"
    )
    additional_description += "\nhttps://github.com/regenie/seqcolapi"

    parser = VersionInHelpParser(
        prog=PKG_NAME, description=banner, epilog=additional_description
    )

    parser.add_argument(
        "-V",
        "--version",
        action="version",
        version="%(prog)s {v}".format(v=seqcolapi_version),
    )

    msg_by_cmd = {"serve": "run the server"}

    subparsers = parser.add_subparsers(dest="command")

    def add_subparser(cmd, description):
        return subparsers.add_parser(cmd, description=description, help=description)

    sps = {}
    # add arguments that are common for all subparsers
    for cmd, desc in msg_by_cmd.items():
        sps[cmd] = add_subparser(cmd, desc)
        sps[cmd].add_argument(
            "-c",
            "--config",
            required=True,
            dest="config",
            help="Path to the seqcolapi config file (YAML).",
        )
        sps[cmd].add_argument(
            "-d",
            "--dbg",
            action="store_true",
            dest="debug",
            help="Set logger verbosity to debug",
        )
    # add subparser-specific arguments
    sps["serve"].add_argument(
        "-p",
        "--port",
        dest="port",
        type=int,
        help="The port the webserver should be run on.",
        default=None,
    )
    return parser
