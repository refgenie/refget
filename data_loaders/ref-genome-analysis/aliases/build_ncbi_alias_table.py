#!/usr/bin/env python3
"""
Build NCBI alias mapping table from assembly reports.

Downloads NCBI assembly_report.txt files for each accession in the inventory
CSV and parses them into a flat CSV mapping sequence names to accessions.

This is Phase A of the alias registration pipeline -- it produces a standalone
CSV with no store dependency. Needs only the inventory CSV and internet access.

Usage:
    python build_ncbi_alias_table.py --inventory refgenomes_inventory.csv
    python build_ncbi_alias_table.py --inventory refgenomes_inventory.csv --limit 3
    python build_ncbi_alias_table.py --inventory refgenomes_inventory.csv --download-only
"""

import argparse
import csv
import os
import re
import sys
import time
import urllib.error
import urllib.request

BRICK_ROOT = "/project/shefflab/brickyard/datasets_downloaded/refgenomes_fasta"
INVENTORY_CSV = f"{BRICK_ROOT}/refgenomes_inventory.csv"
STAGING_DIR = f"{BRICK_ROOT}/refget_staging"
ACCESSION_PATTERN = re.compile(r"(GC[AF]_\d+\.\d+)")
NCBI_FTP_BASE = "https://ftp.ncbi.nlm.nih.gov/genomes/all"

OUTPUT_COLUMNS = [
    "accession",
    "sequence_name",
    "sequence_length",
    "refseq_accn",
    "genbank_accn",
    "ucsc_name",
    "genbank_assembly_accn",
    "refseq_assembly_accn",
]


def parse_args():
    parser = argparse.ArgumentParser(
        description="Download NCBI assembly reports and build alias mapping table."
    )
    parser.add_argument(
        "--inventory", default=INVENTORY_CSV, help="Path to refgenomes_inventory.csv"
    )
    parser.add_argument(
        "--report-cache",
        default=f"{STAGING_DIR}/assembly_reports",
        help="Directory to cache downloaded assembly_report.txt files",
    )
    parser.add_argument(
        "--output",
        default=f"{STAGING_DIR}/ncbi_alias_table.csv",
        help="Output CSV path",
    )
    parser.add_argument(
        "--limit", type=int, default=None, help="Process only first N accessions"
    )
    parser.add_argument(
        "--offset", type=int, default=0, help="Skip first N accessions"
    )
    parser.add_argument(
        "--download-only",
        action="store_true",
        help="Download reports but don't parse into table",
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# Step A2: Read inventory and extract accessions
# ---------------------------------------------------------------------------

def read_accessions_from_inventory(csv_path):
    """Read inventory CSV and return list of (accession, filename) pairs.

    Filters to rows with a non-empty accession matching the GCF_/GCA_ pattern.
    """
    pairs = []
    seen_accessions = set()
    with open(csv_path, newline="") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None:
            print(f"ERROR: {csv_path} appears to be empty", file=sys.stderr)
            sys.exit(1)
        for row in reader:
            accession = row.get("accession", "").strip()
            filename = row.get("filename", "").strip()
            if not accession or not ACCESSION_PATTERN.match(accession):
                continue
            if accession in seen_accessions:
                continue
            seen_accessions.add(accession)
            pairs.append((accession, filename))
    return pairs


# ---------------------------------------------------------------------------
# Step A3: Construct NCBI FTP URLs from filename
# ---------------------------------------------------------------------------

def derive_assembly_name(accession, filename):
    """Derive the assembly name from the FASTA filename.

    Example:
        accession = "GCF_000001405.40"
        filename  = "GCF_000001405.40_GRCh38.p14_genomic.fna.gz"
        returns   "GRCh38.p14"

    The filename pattern is: {accession}_{assembly_name}_genomic.fna[.gz]
    """
    # Strip the accession prefix and _genomic.fna[.gz] suffix
    prefix = accession + "_"
    if not filename.startswith(prefix):
        return None
    rest = filename[len(prefix):]
    # Remove _genomic.fna, _genomic.fna.gz, _genomic.fa.gz, etc.
    rest = re.sub(r"_genomic\.(fna|fa|fasta)(\.gz)?$", "", rest)
    if not rest:
        return None
    return rest


def accession_to_ftp_dir(accession):
    """Convert an accession to its NCBI FTP parent directory URL.

    GCF_963692335.1 -> https://ftp.ncbi.nlm.nih.gov/genomes/all/GCF/963/692/335/
    """
    match = re.match(r"(GC[AF])_(\d+)\.\d+", accession)
    if not match:
        return None
    prefix = match.group(1)
    numeric = match.group(2).zfill(9)
    d1, d2, d3 = numeric[0:3], numeric[3:6], numeric[6:9]
    return f"{NCBI_FTP_BASE}/{prefix}/{d1}/{d2}/{d3}/"


def lookup_assembly_name_from_ftp(accession):
    """Scrape the NCBI FTP directory listing to find the assembly name.

    The directory contains a single subdirectory like GCF_963692335.1_fOsmEpe2.1/.
    We extract the assembly name from that.
    """
    dir_url = accession_to_ftp_dir(accession)
    if not dir_url:
        return None
    try:
        req = urllib.request.Request(dir_url, headers={"User-Agent": "refget-alias-builder/1.0"})
        with urllib.request.urlopen(req, timeout=15) as response:
            html = response.read().decode("utf-8", errors="replace")
        # Look for a link like GCF_963692335.1_fOsmEpe2.1/
        pattern = re.escape(accession) + r"_([^/\"]+)/"
        m = re.search(pattern, html)
        if m:
            return m.group(1)
    except (urllib.error.URLError, urllib.error.HTTPError, OSError):
        pass
    return None


def construct_report_url(accession, assembly_name):
    """Construct the NCBI FTP URL for an assembly_report.txt.

    URL pattern:
        https://ftp.ncbi.nlm.nih.gov/genomes/all/{GCF|GCA}/{d1}/{d2}/{d3}/
        {accession}_{assembly_name}/{accession}_{assembly_name}_assembly_report.txt

    Where d1/d2/d3 are 3-char chunks of the numeric part of the accession
    (the digits between the underscore and the dot).
    """
    dir_url = accession_to_ftp_dir(accession)
    if not dir_url:
        return None
    stem = f"{accession}_{assembly_name}"
    return f"{dir_url}{stem}/{stem}_assembly_report.txt"


# ---------------------------------------------------------------------------
# Step A4: Download with caching and rate limiting
# ---------------------------------------------------------------------------

def download_report(accession, filename, cache_dir, sleep_sec=0.3):
    """Download assembly_report.txt for a given accession.

    Returns (cache_path, status) where status is one of:
        "cached"    - already existed in cache
        "downloaded" - freshly downloaded
        "failed"    - download failed (logged to stderr)
        "skipped"   - could not derive assembly name from filename
    """
    cache_path = os.path.join(cache_dir, f"{accession}_assembly_report.txt")

    # Check cache first
    if os.path.exists(cache_path) and os.path.getsize(cache_path) > 0:
        return cache_path, "cached"

    # Derive assembly name from filename, fall back to FTP directory lookup
    assembly_name = derive_assembly_name(accession, filename)
    if not assembly_name:
        assembly_name = lookup_assembly_name_from_ftp(accession)
        if assembly_name:
            time.sleep(sleep_sec)  # Rate limit the directory lookup too
        else:
            return cache_path, "skipped"

    url = construct_report_url(accession, assembly_name)
    if not url:
        print(f"  WARNING: Cannot construct URL for {accession}", file=sys.stderr)
        return cache_path, "skipped"

    # Download
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "refget-alias-builder/1.0"})
        with urllib.request.urlopen(req, timeout=30) as response:
            data = response.read()
        with open(cache_path, "wb") as f:
            f.write(data)
        time.sleep(sleep_sec)
        return cache_path, "downloaded"
    except (urllib.error.URLError, urllib.error.HTTPError, OSError) as e:
        print(f"  FAILED: {accession} ({url}): {e}", file=sys.stderr)
        return cache_path, "failed"


# ---------------------------------------------------------------------------
# Step A5: Parse reports into flat CSV
# ---------------------------------------------------------------------------

def parse_assembly_report(filepath, accession):
    """Parse an assembly_report.txt file into a list of row dicts.

    Returns (rows, genbank_assembly_accn, refseq_assembly_accn).
    """
    genbank_assembly_accn = ""
    refseq_assembly_accn = ""
    rows = []

    with open(filepath, "r", errors="replace") as f:
        for line in f:
            line = line.rstrip("\n")
            # Parse header metadata
            if line.startswith("#"):
                if "GenBank assembly accession:" in line:
                    m = ACCESSION_PATTERN.search(line)
                    if m:
                        genbank_assembly_accn = m.group(1)
                elif "RefSeq assembly accession:" in line:
                    m = ACCESSION_PATTERN.search(line)
                    if m:
                        refseq_assembly_accn = m.group(1)
                continue

            # Data rows: tab-separated, 10 columns
            fields = line.split("\t")
            if len(fields) < 9:
                continue

            sequence_name = fields[0].strip()
            genbank_accn = fields[4].strip() if len(fields) > 4 else "na"
            refseq_accn = fields[6].strip() if len(fields) > 6 else "na"
            sequence_length = fields[8].strip() if len(fields) > 8 else "na"
            ucsc_name = fields[9].strip() if len(fields) > 9 else "na"

            # Normalize "na" to empty string
            if genbank_accn == "na":
                genbank_accn = ""
            if refseq_accn == "na":
                refseq_accn = ""
            if ucsc_name == "na":
                ucsc_name = ""
            if sequence_length == "na":
                sequence_length = ""

            rows.append({
                "accession": accession,
                "sequence_name": sequence_name,
                "sequence_length": sequence_length,
                "refseq_accn": refseq_accn,
                "genbank_accn": genbank_accn,
                "ucsc_name": ucsc_name,
                "genbank_assembly_accn": genbank_assembly_accn,
                "refseq_assembly_accn": refseq_assembly_accn,
            })

    return rows


def write_alias_table(output_path, all_rows):
    """Write the alias table CSV."""
    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=OUTPUT_COLUMNS)
        writer.writeheader()
        writer.writerows(all_rows)


def main():
    args = parse_args()

    # Step A2: Read inventory and extract accessions
    print(f"Reading inventory from {args.inventory}", file=sys.stderr)
    pairs = read_accessions_from_inventory(args.inventory)
    print(f"Found {len(pairs)} unique accessions", file=sys.stderr)

    # Apply offset and limit
    if args.offset:
        pairs = pairs[args.offset:]
        print(f"Skipped first {args.offset} accessions", file=sys.stderr)
    if args.limit:
        pairs = pairs[: args.limit]
        print(f"Limited to {args.limit} accessions", file=sys.stderr)

    # Create cache directory
    os.makedirs(args.report_cache, exist_ok=True)

    # Step A4: Download reports
    n_cached = 0
    n_downloaded = 0
    n_failed = 0
    n_skipped = 0
    downloaded_reports = []  # (accession, cache_path)

    print(f"\nDownloading assembly reports...", file=sys.stderr)
    for i, (accession, filename) in enumerate(pairs, 1):
        print(
            f"[{i}/{len(pairs)}] {accession}...",
            end=" ",
            flush=True,
            file=sys.stderr,
        )
        cache_path, status = download_report(accession, filename, args.report_cache)
        print(status, file=sys.stderr)

        if status == "cached":
            n_cached += 1
            downloaded_reports.append((accession, cache_path))
        elif status == "downloaded":
            n_downloaded += 1
            downloaded_reports.append((accession, cache_path))
        elif status == "failed":
            n_failed += 1
        elif status == "skipped":
            n_skipped += 1

    print(
        f"\nDownload summary: {n_downloaded} downloaded, {n_cached} cached, "
        f"{n_failed} failed, {n_skipped} skipped",
        file=sys.stderr,
    )

    if args.download_only:
        print("--download-only specified, stopping before parsing.", file=sys.stderr)
        return

    # Step A5: Parse reports into flat CSV
    print(f"\nParsing assembly reports...", file=sys.stderr)
    all_rows = []
    n_parsed = 0
    for accession, cache_path in downloaded_reports:
        if not os.path.exists(cache_path) or os.path.getsize(cache_path) == 0:
            continue
        rows = parse_assembly_report(cache_path, accession)
        all_rows.extend(rows)
        n_parsed += 1

    write_alias_table(args.output, all_rows)

    # Summary
    print(f"\nResults:", file=sys.stderr)
    print(f"  Accessions processed: {len(pairs)}", file=sys.stderr)
    print(f"  Reports parsed: {n_parsed}", file=sys.stderr)
    print(f"  Total sequence rows: {len(all_rows)}", file=sys.stderr)
    print(f"  Output written to: {args.output}", file=sys.stderr)


if __name__ == "__main__":
    main()
