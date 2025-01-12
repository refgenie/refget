import henge
import json
import os
import logging
import requests
import yaml

from yacman import load_yaml
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
    add_fasta = subparsers.add_parser("add_fasta", help="Add a fasta file to the database")
    add_fasta.add_argument("fasta_file", help="Path to the fasta file")
    return parser


def main():
    parser = build_argparser()
    args = parser.parse_args()
    print(args)

    if args.command == "add-fasta":
        print("Adding fasta file")
        print(args.fasta_file)
        refget = RefgetDBAgent()
        refget.seqcol.add_from_fasta_file(args.fasta_file)
        print("Added fasta file")
    else:
        print("No command given")
