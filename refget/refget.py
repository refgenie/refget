import henge
import json
import os
import logging
import requests

from copy import copy

from .agents import RefgetDBAgent

_LOGGER = logging.getLogger(__name__)

henge.ITEM_TYPE = "_item_type"
SCHEMA_FILEPATH = os.path.join(os.path.dirname(__file__), "schemas")

sequence_schema = """description: "Schema for a single raw sequence"
henge_class: sequence
type: string
description: "Actual sequence content"
"""


def build_argparser():
    from . import __version__

    version_str = f"{__version__} "
    from ubiquerg import VersionInHelpParser

    additional_description = "https://refgenie.org/refget"
    banner = f"%(prog)s - a tool for getting sequences by digest"
    parser = VersionInHelpParser(
        prog="refget",
        description=banner,
        epilog=additional_description,
        version=version_str,
    )
    subparsers = parser.add_subparsers(dest="command")

    add_fasta = subparsers.add_parser("add-fasta", help="Add a fasta file to the database")
    add_fasta.add_argument("--fasta-file", help="Path to the fasta file", default=None)
    add_fasta.add_argument(
        "--pep", "-p", help="Set to input a pep of FASTA files", type=str, default=False
    )
    add_fasta.add_argument("--fa-root", "-r", help="Root directory for fasta files", default="")

    digest_fasta = subparsers.add_parser("digest-fasta", help="Digest a fasta file")
    digest_fasta.add_argument("fasta_file", help="Path to the fasta file")
    digest_fasta.add_argument(
        "--level", "-l", help="Output level, one of 0, 1 or 2 (default).", default=2, type=int
    )

    return parser


class BytesEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, bytes):
            return obj.decode(errors="ignore")  # or use base64 encoding
        return super().default(obj)


def main(injected_args=None):
    parser = build_argparser()
    args = parser.parse_args()
    _LOGGER.debug(args)

    if not args.command:
        parser.print_help()
        return
    if args.command == "add-fasta":
        if args.pep:
            _LOGGER.info(f"Adding fasta file from PEP: {args.pep}")
            import peppy

            p = peppy.Project(args.pep)
            agent = RefgetDBAgent()
            result = agent.seqcol.add_from_fasta_pep(p, args.fa_root)
            print(json.dumps(result, indent=2, cls=BytesEncoder))
        if args.fasta_file:
            _LOGGER.info(f"Adding fasta file: {args.fasta_file}")
            agent = RefgetDBAgent()
            agent.seqcol.add_from_fasta_file(args.fasta_file)
            _LOGGER.info("Added fasta file")
    elif args.command == "digest-fasta":
        _LOGGER.info(f"Digesting fasta file: {args.fasta_file}")
        if args.level == 0:
            from .utilities import fasta_to_digest

            digest = fasta_to_digest(args.fasta_file)
            print(digest)
        elif args.level == 1:
            from .utilities import fasta_to_seqcol_dict, seqcol_dict_to_level1_dict

            seqcol_dict = fasta_to_seqcol_dict(args.fasta_file)
            level1_dict = seqcol_dict_to_level1_dict(seqcol_dict)
            print(json.dumps(level1_dict, indent=2))
        elif args.level == 2:
            from .utilities import fasta_to_seqcol_dict

            seqcol_dict = fasta_to_seqcol_dict(args.fasta_file)
            print(json.dumps(seqcol_dict, indent=2, cls=BytesEncoder))
    else:
        print("No command given")
