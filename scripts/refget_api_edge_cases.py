#!/usr/bin/env python3
"""Probe a live refget Sequences API for start/end edge-case behavior.

This is an exploratory / diagnostic script, NOT a pytest unit test. It sends
real HTTP requests to a public refget server (by default the EBI ENA refget
endpoint at https://www.ebi.ac.uk/ena/cram) to observe how it actually handles
corner cases of the `start`/`end` query parameters and HTTP `Range` headers:

  - using `start` or `end` independently
  - `end` greater than, equal to, and one past the sequence length
  - `start` greater than or equal to the sequence length
  - equivalent `Range: bytes=...` header requests

The script prints each response status/body and a summary table comparing the
observed behavior against the RFC 7233 expectations, to help inform the spec
discussion. It does not assert anything; you interpret the printed output.

Related GA4GH refget spec issue:
  #107 "Refget Sequences start/end query parameter and range request corner cases"
  https://github.com/ga4gh/refget/issues/107

Usage:
  python scripts/refget_api_edge_cases.py

Requires the `requests` package and network access. The default test sequence
is the trivial sequence "ACGT" (md5 f1f8f4bf413b16ad135722aa4591043e, length 4).
"""

import requests

BASE_URL = "https://www.ebi.ac.uk/ena/cram"
SEQ_ID = "f1f8f4bf413b16ad135722aa4591043e"  # ACGT, length 4
SEQ_LENGTH = 4


def test_case(name, url, headers=None):
    """Run a test case and return results."""
    try:
        resp = requests.get(url, headers=headers or {}, timeout=30)
        return {
            "name": name,
            "status": resp.status_code,
            "content": resp.text,
        }
    except Exception as e:
        return {"name": name, "error": str(e)}


def main():
    print("=" * 70)
    print("Refget Sequence API Edge Case Tests (Issue #107)")
    print(f"Server: {BASE_URL}")
    print(f"Sequence: {SEQ_ID} (content: ACGT, length: {SEQ_LENGTH})")
    print("=" * 70)

    tests = [
        # Baseline
        ("Full sequence (no params)", f"{BASE_URL}/sequence/{SEQ_ID}", None),
        ("Both start=1 and end=3", f"{BASE_URL}/sequence/{SEQ_ID}?start=1&end=3", None),
        # Independent parameter tests
        ("start only (start=2)", f"{BASE_URL}/sequence/{SEQ_ID}?start=2", None),
        ("end only (end=2)", f"{BASE_URL}/sequence/{SEQ_ID}?end=2", None),
        # Out of bounds end tests
        ("end > length (end=100)", f"{BASE_URL}/sequence/{SEQ_ID}?start=0&end=100", None),
        ("end = length (end=4)", f"{BASE_URL}/sequence/{SEQ_ID}?start=0&end=4", None),
        ("end = length+1 (end=5)", f"{BASE_URL}/sequence/{SEQ_ID}?start=0&end=5", None),
        # Out of bounds start tests
        ("start > length (start=100)", f"{BASE_URL}/sequence/{SEQ_ID}?start=100&end=101", None),
        ("start = length (start=4)", f"{BASE_URL}/sequence/{SEQ_ID}?start=4&end=5", None),
        # Range header tests
        ("Range: bytes=0-1", f"{BASE_URL}/sequence/{SEQ_ID}", {"Range": "bytes=0-1"}),
        ("Range: bytes=2-99 (end>len)", f"{BASE_URL}/sequence/{SEQ_ID}", {"Range": "bytes=2-99"}),
        (
            "Range: bytes=99-100 (start>len)",
            f"{BASE_URL}/sequence/{SEQ_ID}",
            {"Range": "bytes=99-100"},
        ),
    ]

    results = []
    for name, url, headers in tests:
        result = test_case(name, url, headers)
        results.append(result)

        print(f"\n### {name}")
        if headers:
            print(f"Headers: {headers}")
        if "error" in result:
            print(f"ERROR: {result['error']}")
        else:
            print(f"Status: {result['status']} | Content: '{result['content']}'")

    # Summary table
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"{'Test Case':<35} {'Status':<8} {'Content':<15} {'Interpretation'}")
    print("-" * 70)

    for r in results:
        if "error" in r:
            interp = "ERROR"
            content = "N/A"
            status = "ERR"
        else:
            status = r["status"]
            content = f"'{r['content']}'" if r["content"] else "(empty)"
            if status == 200:
                interp = "OK"
            elif status == 206:
                interp = "Partial Content"
            elif status == 400:
                interp = "Bad Request (rejected)"
            elif status == 416:
                interp = "Range Not Satisfiable"
            elif status == 501:
                interp = "Not Implemented"
            else:
                interp = "Other"

        print(f"{r['name']:<35} {status:<8} {content:<15} {interp}")

    print("\n" + "=" * 70)
    print("RFC 7233 Expected Behavior:")
    print("  - end > length: CLIP to length (return data)")
    print("  - start > length: 416 Range Not Satisfiable (for Range header)")
    print("  - start > length: 400 Bad Request (for query params per spec)")
    print("=" * 70)


if __name__ == "__main__":
    main()
