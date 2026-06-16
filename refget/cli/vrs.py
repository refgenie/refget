"""
VRS (GA4GH Variation Representation) commands for the refget CLI.

Computes VRS Allele identifiers for variants in a VCF file by normalizing
each variant against a reference sequence collection held in a RefgetStore.

Commands:
    compute - Compute VRS Allele identifiers for variants in a VCF
"""

import json
from pathlib import Path
from typing import Optional

import typer

from refget.cli.output import (
    EXIT_SUCCESS,
    print_json,
)
from refget.cli.store import _ensure_collection_loaded, _load_store

app = typer.Typer(
    name="vrs",
    help="VRS allele identifier computation",
    no_args_is_help=True,
)


@app.command()
def compute(
    digest: str = typer.Argument(
        ...,
        help="Collection digest of the reference assembly to normalize against",
    ),
    vcf: Path = typer.Argument(
        ...,
        help="Path to a plain-text VCF file",
        exists=True,
        readable=True,
    ),
    output: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help="Write JSON results to a file (default: stdout)",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        "-j",
        help="Emit a JSON list instead of tab-separated lines",
    ),
    path: Optional[Path] = typer.Option(
        None,
        "--path",
        "-p",
        help="Store path (default: from config)",
    ),
    remote: Optional[str] = typer.Option(
        None,
        "--remote",
        "-r",
        help="Remote store URL (overrides --path)",
    ),
) -> None:
    """
    Compute GA4GH VRS Allele identifiers for variants in a VCF file.

    Each variant is normalized against the reference sequence (taken from the
    given collection in the store) and a VRS digest is computed. Each result
    has keys: chrom, pos, ref, alt, vrs_id.

    Default output is one variant per line as:
        chrom<TAB>pos<TAB>ref<TAB>alt<TAB>vrs_id
    Use --json (or --output) to emit/write the full JSON list.

    Examples:
        refget vrs compute <coll_digest> variants.vcf
        refget vrs compute <coll_digest> variants.vcf --json
        refget vrs compute <coll_digest> variants.vcf -o vrs.json
    """
    store = _load_store(path, remote=remote)
    _ensure_collection_loaded(store, digest)
    store.load_all_sequences()

    results = store.compute_vrs_ids(digest, str(vcf.resolve()))

    if output is not None:
        output.write_text(json.dumps(results, indent=2) + "\n")
        print_json({"output": str(output.resolve()), "count": len(results)})
        raise typer.Exit(EXIT_SUCCESS)

    if json_output:
        print_json(results)
    else:
        lines = [
            f"{r['chrom']}\t{r['pos']}\t{r['ref']}\t{r['alt']}\t{r['vrs_id']}"
            for r in results
        ]
        if lines:
            print("\n".join(lines))

    raise typer.Exit(EXIT_SUCCESS)
