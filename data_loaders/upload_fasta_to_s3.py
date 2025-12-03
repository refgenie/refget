"""
Utility script to upload FASTA files to S3.
Uses the same input patterns as the refget FASTA loading functions.

Requires: boto3 (install separately: pip install boto3)
"""

import os


def upload_fasta_file(fasta_file_path: str, bucket: str, prefix: str = "") -> str:
    """
    Upload a single FASTA file to S3.

    Args:
        fasta_file_path: Path to the FASTA file
        bucket: S3 bucket name
        prefix: Optional prefix/folder in the bucket

    Returns:
        str: The S3 URL of the uploaded file
    """
    import boto3

    s3 = boto3.client("s3")
    key = (
        os.path.join(prefix, os.path.basename(fasta_file_path))
        if prefix
        else os.path.basename(fasta_file_path)
    )
    s3.upload_file(fasta_file_path, bucket, key)
    return f"https://{bucket}.s3.amazonaws.com/{key}"


def upload_fasta_pep(pep, fa_root: str, bucket: str, prefix: str = "") -> dict:
    """
    Upload FASTA files from a PEP to S3.
    Same interface as SequenceCollectionAgent.add_from_fasta_pep.

    Args:
        pep: peppy.Project object
        fa_root: Root directory containing the FASTA files
        bucket: S3 bucket name
        prefix: Optional prefix/folder in the bucket

    Returns:
        dict: Mapping of FASTA filenames to S3 URLs
    """
    results = {}
    for s in pep.samples:
        fa_path = os.path.join(fa_root, s.fasta)
        url = upload_fasta_file(fa_path, bucket, prefix)
        results[s.fasta] = url
    return results


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Upload FASTA files to S3")
    parser.add_argument("--fasta-file", help="Single FASTA file to upload")
    parser.add_argument("--pep", help="PEP file for batch upload")
    parser.add_argument("--fa-root", help="Root directory for FASTA files (with --pep)")
    parser.add_argument("--bucket", required=True, help="S3 bucket name")
    parser.add_argument("--prefix", default="", help="S3 key prefix")
    args = parser.parse_args()

    if args.fasta_file:
        url = upload_fasta_file(args.fasta_file, args.bucket, args.prefix)
        print(f"Uploaded to: {url}")
    elif args.pep:
        import peppy

        pep = peppy.Project(args.pep)
        results = upload_fasta_pep(pep, args.fa_root, args.bucket, args.prefix)
        for fasta, url in results.items():
            print(f"{fasta}: {url}")
    else:
        print("Error: Must provide either --fasta-file or --pep")
        parser.print_help()
