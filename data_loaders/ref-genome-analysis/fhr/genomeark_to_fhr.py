#!/usr/bin/env python3
"""Generate FHR metadata JSON files from GenomeArk + NCBI Datasets API.

Given a GCA accession, fetches:
  1. Assembly metadata from NCBI Datasets API (taxonomy, stats, sequencing tech)
  2. Species metadata from GenomeArk GitHub repo (common name, genome size, project)

Outputs an FHR-compatible JSON file that can be loaded into a RefgetStore via
store.load_fhr_metadata(digest, path).

Usage:
    python genomeark_to_fhr.py GCA_964261635.1 [output.fhr.json]
    python genomeark_to_fhr.py GCA_964261635.1 GCA_964263255.1  # multiple accessions
"""

import json
import sys
import urllib.request
from pathlib import Path


def fetch_ncbi_report(accession: str) -> dict:
    """Fetch assembly report from NCBI Datasets API."""
    url = f"https://api.ncbi.nlm.nih.gov/datasets/v2/genome/accession/{accession}/dataset_report"
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read())
    reports = data.get("reports", [])
    if not reports:
        raise ValueError(f"No assembly report found for {accession}")
    return reports[0]


def fetch_genomeark_yaml(species_name: str) -> dict | None:
    """Fetch species YAML from genomeark-metadata GitHub repo."""
    filename = species_name.replace(" ", "_")
    url = f"https://raw.githubusercontent.com/genomeark/genomeark-metadata/main/species/{filename}.yaml"
    try:
        import yaml
    except ImportError:
        # Fall back to basic parsing if PyYAML not available
        try:
            with urllib.request.urlopen(url) as resp:
                text = resp.read().decode()
            # Basic extraction without full YAML parsing
            result = {"_raw": text}
            for line in text.split("\n"):
                line = line.strip()
                if line.startswith("common_name:"):
                    result["common_name"] = line.split(":", 1)[1].strip().strip("'\"")
                elif line.startswith("genome_size:"):
                    try:
                        result["genome_size"] = int(line.split(":", 1)[1].strip())
                    except ValueError:
                        pass
                elif line.startswith("project:"):
                    result["project"] = line.split(":", 1)[1].strip()
            return result
        except Exception:
            return None

    try:
        with urllib.request.urlopen(url) as resp:
            return yaml.safe_load(resp.read())
    except Exception:
        return None


def ncbi_to_fhr(report: dict, genomeark: dict | None = None) -> dict:
    """Convert NCBI assembly report + GenomeArk data to FHR metadata."""
    organism = report.get("organism", {})
    assembly = report.get("assembly_info", {})
    stats = report.get("assembly_stats", {})

    species_name = organism.get("organism_name", "")
    tax_id = organism.get("tax_id")
    common_name = organism.get("common_name", "")

    # GenomeArk may have a better common name
    if genomeark:
        species = genomeark.get("species", genomeark)
        common_name = common_name or species.get("common_name", "")

    fhr = {
        "schema": "https://raw.githubusercontent.com/FAIR-bioHeaders/FHR-Specification/main/fhr.json",
        "schemaVersion": 1,
        "genome": species_name,
        "version": assembly.get("assembly_name", ""),
        "dateCreated": assembly.get("release_date", ""),
    }

    # Taxonomy
    if tax_id:
        fhr["taxon"] = {
            "name": species_name,
            "uri": f"https://identifiers.org/taxonomy:{tax_id}",
        }

    # Common name as synonym
    if common_name:
        fhr["genomeSynonym"] = [common_name]

    # Accession
    accession = report.get("accession", "")
    if accession:
        fhr["accessionID"] = {
            "name": accession,
            "url": f"https://www.ncbi.nlm.nih.gov/datasets/genome/{accession}/",
        }

    # Submitter as assembly author
    submitter = assembly.get("submitter", "")
    if submitter:
        fhr["assemblyAuthor"] = [{"name": submitter}]

    # Sequencing technology
    seq_tech = assembly.get("sequencing_tech", "")
    if seq_tech:
        fhr["instrument"] = [t.strip() for t in seq_tech.split(",")]

    # Assembly method
    method = assembly.get("assembly_method", "")
    if method and method != "various":
        fhr["assemblySoftware"] = method

    # Vital statistics
    vital = {}
    if stats.get("contig_n50"):
        vital["N50"] = stats["contig_n50"]
    if stats.get("contig_l50"):
        vital["L50"] = stats["contig_l50"]
    if stats.get("total_sequence_length"):
        vital["totalBasePairs"] = int(stats["total_sequence_length"])
    if stats.get("number_of_contigs"):
        vital["numberContigs"] = stats["number_of_contigs"]
    if stats.get("number_of_scaffolds"):
        vital["numberScaffolds"] = stats["number_of_scaffolds"]
    if stats.get("scaffold_n50"):
        vital["scaffoldN50"] = stats["scaffold_n50"]
    if vital:
        fhr["vitalStats"] = vital

    # Related links
    links = []
    links.append(f"https://www.genomeark.org/genomeark-all/{species_name.replace(' ', '_')}.html")
    if accession:
        links.append(f"https://www.ncbi.nlm.nih.gov/datasets/genome/{accession}/")
    fhr["relatedLink"] = links

    # BioProject lineage — note VGP/DToL/EBP affiliations
    projects = []
    for lineage in assembly.get("bioproject_lineage", []):
        for bp in lineage.get("bioprojects", []):
            title = bp.get("title", "")
            if any(kw in title.lower() for kw in ["vertebrate genomes", "darwin tree", "earth biogenome"]):
                projects.append(title)
    if projects:
        fhr["documentation"] = "Projects: " + "; ".join(projects)

    # License
    fhr["license"] = "https://www.genomeark.org/documentation/data-use-policy.html"

    return fhr


def process_accession(accession: str, output_path: str | None = None) -> str:
    """Process a single accession and write FHR JSON."""
    print(f"Fetching NCBI report for {accession}...", file=sys.stderr)
    report = fetch_ncbi_report(accession)

    species_name = report.get("organism", {}).get("organism_name", "")
    print(f"  Species: {species_name}", file=sys.stderr)

    print(f"  Fetching GenomeArk metadata...", file=sys.stderr)
    genomeark = fetch_genomeark_yaml(species_name) if species_name else None

    fhr = ncbi_to_fhr(report, genomeark)

    if output_path is None:
        output_path = f"{accession}.fhr.json"

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(fhr, f, indent=2)

    print(f"  Wrote: {output_path}", file=sys.stderr)
    return output_path


def main():
    if len(sys.argv) < 2:
        print("Usage: genomeark_to_fhr.py <accession> [accession2 ...] [--output-dir DIR]")
        print("       genomeark_to_fhr.py GCA_964261635.1")
        print("       genomeark_to_fhr.py GCA_964261635.1 GCA_964263255.1 --output-dir fhr/")
        sys.exit(1)

    args = sys.argv[1:]
    output_dir = None

    if "--output-dir" in args:
        idx = args.index("--output-dir")
        output_dir = args[idx + 1]
        args = args[:idx] + args[idx + 2:]

    for accession in args:
        if output_dir:
            output_path = f"{output_dir}/{accession}.fhr.json"
        else:
            output_path = f"{accession}.fhr.json"
        process_accession(accession, output_path)


if __name__ == "__main__":
    main()
