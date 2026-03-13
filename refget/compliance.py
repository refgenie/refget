"""
GA4GH SeqCol API Compliance Suite.

This is THE canonical compliance suite. It can be run two ways:
1. Via pytest: tests/api/test_compliance.py wraps these checks
2. Via web UI: /compliance/stream endpoint streams results in real-time

All check functions take an api_root URL and raise AssertionError on failure.
The runner functions execute checks and return structured results.

Test data is loaded from test_fasta/test_fasta_digests.json and
tests/api/comparison/ fixture files relative to the repository root.
"""

import json
import logging
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path

import requests

_LOGGER = logging.getLogger(__name__)

COMPLIANCE_TIMEOUT = 3  # seconds per request

# ============================================================
# Test data -- loaded from repository fixtures
# ============================================================

REPO_ROOT = Path(__file__).parent.parent
_DIGESTS_FILE = REPO_ROOT / "test_fasta" / "test_fasta_digests.json"
_COMPARISON_DIR = REPO_ROOT / "tests" / "api" / "comparison"

# Load digest test data
with open(_DIGESTS_FILE) as _f:
    DIGEST_DATA = json.load(_f)

# Convert to list of (name, bundle) tuples for iteration
DIGEST_TESTS = [(name, bundle) for name, bundle in DIGEST_DATA.items()]

# Comparison fixture files (base.fa vs each other file)
COMPARISON_FILES = [
    _COMPARISON_DIR / "compare_base.fa_subset.fa.json",
    _COMPARISON_DIR / "compare_base.fa_different_names.fa.json",
    _COMPARISON_DIR / "compare_base.fa_different_order.fa.json",
    _COMPARISON_DIR / "compare_base.fa_pair_swap.fa.json",
    _COMPARISON_DIR / "compare_base.fa_swap_wo_coords.fa.json",
]

# Load comparison fixtures
COMPARISON_FIXTURES = {}
for _f in COMPARISON_FILES:
    with open(_f) as _fp:
        COMPARISON_FIXTURES[_f.name] = json.load(_fp)


# ============================================================
# Result types
# ============================================================


@dataclass
class CheckResult:
    """Result of a single compliance check."""

    name: str
    passed: bool
    duration_ms: float
    description: str | None = None
    message: str | None = None
    error: str | None = None


@dataclass
class ComplianceReport:
    """Full compliance report for a server."""

    server_url: str
    timestamp: str
    total: int = 0
    passed: int = 0
    failed: int = 0
    errors: int = 0
    results: list[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


def _timed_check(name: str, func, *args, **kwargs) -> CheckResult:
    """Run a check function and capture timing and errors."""
    description = (func.__doc__ or "").strip().split("\n")[0] or None
    start = time.monotonic()
    try:
        func(*args, **kwargs)
        elapsed = (time.monotonic() - start) * 1000
        return CheckResult(
            name=name, passed=True, duration_ms=round(elapsed, 2), description=description
        )
    except AssertionError as e:
        elapsed = (time.monotonic() - start) * 1000
        return CheckResult(
            name=name,
            passed=False,
            duration_ms=round(elapsed, 2),
            description=description,
            error=str(e),
        )
    except requests.exceptions.RequestException as e:
        elapsed = (time.monotonic() - start) * 1000
        return CheckResult(
            name=name,
            passed=False,
            duration_ms=round(elapsed, 2),
            description=description,
            error=f"Connection error: {e}",
        )
    except Exception as e:
        elapsed = (time.monotonic() - start) * 1000
        return CheckResult(
            name=name,
            passed=False,
            duration_ms=round(elapsed, 2),
            description=description,
            error=f"Unexpected error: {e}",
        )


# ============================================================
# Structure checks -- validate response format
# ============================================================


def check_service_info(api_root):
    """Service-info returns required GA4GH fields and seqcol schema."""
    res = requests.get(f"{api_root}/service-info", timeout=COMPLIANCE_TIMEOUT)
    data = res.json()
    assert "id" in data, "service-info missing 'id' field"
    assert "type" in data, "service-info missing 'type' field"
    assert "group" in data["type"], "service-info type missing 'group'"
    assert "artifact" in data["type"], "service-info type missing 'artifact'"
    assert "version" in data["type"], "service-info type missing 'version'"
    assert "seqcol" in data, "service-info must have 'seqcol' section"
    assert "schema" in data["seqcol"], "seqcol section must include 'schema'"
    schema = data["seqcol"]["schema"]
    assert "properties" in schema, "schema must have 'properties'"
    assert "lengths" in schema["properties"], "schema must define 'lengths'"
    assert "names" in schema["properties"], "schema must define 'names'"
    assert "sequences" in schema["properties"], "schema must define 'sequences'"


def check_list_collections(api_root):
    """List collections returns paginated results with total count."""
    res = requests.get(f"{api_root}/list/collection", timeout=COMPLIANCE_TIMEOUT)
    data = res.json()
    assert "results" in data, "list/collection missing 'results' field"
    assert isinstance(data["results"], list), "list/collection 'results' should be a list"
    assert "pagination" in data, "list/collection missing 'pagination' field"
    assert "page" in data["pagination"], "pagination missing 'page'"
    assert "page_size" in data["pagination"], "pagination missing 'page_size'"
    assert "total" in data["pagination"], "pagination must include 'total' per GA4GH spec"
    assert isinstance(data["pagination"]["total"], int), "pagination 'total' must be an integer"


def check_list_attributes(api_root, attribute_name):
    """List attributes endpoint returns paginated results."""
    res = requests.get(f"{api_root}/list/attributes/{attribute_name}", timeout=COMPLIANCE_TIMEOUT)
    data = res.json()
    assert "results" in data, f"list/attributes/{attribute_name} missing 'results' field"
    assert isinstance(data["results"], list), (
        f"list/attributes/{attribute_name} 'results' should be a list"
    )


def check_openapi_available(api_root):
    """OpenAPI endpoint is available (RECOMMENDED by spec Section 3.6)."""
    res = requests.get(f"{api_root}/openapi.json", timeout=COMPLIANCE_TIMEOUT)
    assert res.status_code == 200, f"OpenAPI endpoint returned status {res.status_code}"
    data = res.json()
    assert "openapi" in data, "OpenAPI response missing 'openapi' field"


# ============================================================
# Collection checks -- verify content against known test data
# ============================================================


def check_collection_level1(api_root, fa_name, bundle):
    """Level 1 response returns digest strings for all attributes."""
    digest = bundle["top_level_digest"]
    res = requests.get(f"{api_root}/collection/{digest}?level=1", timeout=COMPLIANCE_TIMEOUT)
    assert res.status_code == 200, (
        f"Collection {digest} returned HTTP {res.status_code} (expected 200)"
    )
    data = res.json()
    for attr in ["names", "lengths", "sequences"]:
        assert isinstance(data[attr], str), (
            f"Level 1 {attr} should be digest string, got {type(data[attr]).__name__}: {data[attr]}"
        )
        assert data[attr] == bundle["level1"][attr], (
            f"Level 1 {attr} for {fa_name}: expected {bundle['level1'][attr]}, got {data[attr]}"
        )
    assert "sorted_name_length_pairs" in data, "Level 1 missing sorted_name_length_pairs"


def check_collection_level2(api_root, fa_name, bundle):
    """Level 2 response returns arrays matching expected content."""
    digest = bundle["top_level_digest"]
    res = requests.get(f"{api_root}/collection/{digest}?level=2", timeout=COMPLIANCE_TIMEOUT)
    assert res.status_code == 200, (
        f"Collection {digest} returned HTTP {res.status_code} (expected 200)"
    )
    data = res.json()
    for attr in ["names", "lengths", "sequences"]:
        assert isinstance(data[attr], list), (
            f"Level 2 {attr} should be array, got {type(data[attr]).__name__}"
        )
        assert data[attr] == bundle["level2"][attr], (
            f"Level 2 {attr} for {fa_name}: expected {bundle['level2'][attr]}, got {data[attr]}"
        )
    assert "sorted_name_length_pairs" not in data, (
        "Level 2 should not have sorted_name_length_pairs"
    )


def check_default_level_returns_level2(api_root, fa_name, bundle):
    """Collection without ?level= param returns level 2 arrays (spec default)."""
    digest = bundle["top_level_digest"]
    res = requests.get(f"{api_root}/collection/{digest}", timeout=COMPLIANCE_TIMEOUT)
    assert res.status_code == 200, (
        f"Collection {digest} returned HTTP {res.status_code} (expected 200)"
    )
    data = res.json()
    for attr in ["names", "lengths", "sequences"]:
        assert isinstance(data[attr], list), (
            f"Default level for {fa_name} {attr} should be array, got {type(data[attr]).__name__}"
        )


def check_sorted_name_length_pairs(api_root, fa_name, bundle):
    """Level 1 sorted_name_length_pairs digest matches expected value."""
    digest = bundle["top_level_digest"]
    res = requests.get(f"{api_root}/collection/{digest}?level=1", timeout=COMPLIANCE_TIMEOUT)
    assert res.status_code == 200, (
        f"Collection {digest} returned HTTP {res.status_code} (expected 200)"
    )
    data = res.json()
    expected = bundle["sorted_name_length_pairs_digest"]
    actual = data.get("sorted_name_length_pairs")
    assert actual == expected, f"SNLP for {fa_name}: expected {expected}, got {actual}"


# ============================================================
# Attribute checks -- verify attribute retrieval
# ============================================================


def check_attribute_retrieval(api_root, fa_name, bundle, attr_name):
    """Attribute endpoint returns correct array for a known digest."""
    attr_digest = bundle["level1"][attr_name]
    expected = bundle["level2"][attr_name]
    res = requests.get(
        f"{api_root}/attribute/collection/{attr_name}/{attr_digest}", timeout=COMPLIANCE_TIMEOUT
    )
    assert res.status_code == 200, (
        f"Attribute {attr_name}/{attr_digest} returned HTTP {res.status_code} (expected 200)"
    )
    actual = res.json()
    assert actual == expected, (
        f"Attribute {attr_name} for {fa_name}: expected {expected}, got {actual}"
    )


def check_transient_attribute_not_served(api_root):
    """Transient attributes (sorted_name_length_pairs) return 404 from /attribute."""
    bundle = DIGEST_TESTS[0][1]
    digest = bundle["top_level_digest"]
    level1 = requests.get(
        f"{api_root}/collection/{digest}?level=1", timeout=COMPLIANCE_TIMEOUT
    ).json()
    snlp_digest = level1["sorted_name_length_pairs"]
    res = requests.get(
        f"{api_root}/attribute/collection/sorted_name_length_pairs/{snlp_digest}",
        timeout=COMPLIANCE_TIMEOUT,
    )
    assert res.status_code == 404, (
        "Transient attributes should not be served by /attribute endpoint"
    )


# ============================================================
# List/filter checks -- verify filtering and pagination
# ============================================================


def check_list_filter_by_attribute(api_root, fa_name, bundle, attr_name):
    """List collections filtered by attribute digest returns the expected collection."""
    attr_digest = bundle["level1"][attr_name]
    top_digest = bundle["top_level_digest"]
    res = requests.get(
        f"{api_root}/list/collection?{attr_name}={attr_digest}", timeout=COMPLIANCE_TIMEOUT
    )
    assert res.status_code == 200, f"List filter returned HTTP {res.status_code}"
    data = res.json()
    assert "results" in data, "Filtered list missing 'results'"
    assert top_digest in data["results"], (
        f"Collection {top_digest} not in results when filtering by {attr_name}={attr_digest} for {fa_name}. "
        f"Got {len(data['results'])} results: {data['results'][:5]}"
    )


def check_list_multi_attribute_filter_and(api_root):
    """Multiple filter attributes use AND logic (spec Section 3.4)."""
    bundle = DIGEST_TESTS[0][1]
    names_digest = bundle["level1"]["names"]
    lengths_digest = bundle["level1"]["lengths"]
    data = requests.get(
        f"{api_root}/list/collection?names={names_digest}&lengths={lengths_digest}",
        timeout=COMPLIANCE_TIMEOUT,
    ).json()
    assert bundle["top_level_digest"] in data["results"], (
        "AND filter should return base.fa collection"
    )


# ============================================================
# Comparison checks -- verify comparison endpoint
# ============================================================


def check_comparison(api_root, fixture_name, expected):
    """GET comparison returns correct diff structure matching fixture data."""
    url = f"{api_root}/comparison/{expected['digests']['a']}/{expected['digests']['b']}"
    res = requests.get(url, timeout=COMPLIANCE_TIMEOUT)
    assert res.status_code == 200, f"Comparison returned HTTP {res.status_code} for {fixture_name}"
    import refget

    actual = res.json()
    assert refget.canonical_str(actual) == refget.canonical_str(expected), (
        f"Comparison mismatch for {fixture_name}.\n"
        f"  Expected attributes: {expected.get('attributes')}\n"
        f"  Got attributes: {actual.get('attributes')}"
    )


def check_comparison_structure(api_root):
    """Comparison response has all required fields (digests, attributes, array_elements)."""
    digest_a = DIGEST_TESTS[0][1]["top_level_digest"]
    digest_b = DIGEST_TESTS[1][1]["top_level_digest"]
    data = requests.get(
        f"{api_root}/comparison/{digest_a}/{digest_b}", timeout=COMPLIANCE_TIMEOUT
    ).json()
    assert "digests" in data and "a" in data["digests"] and "b" in data["digests"]
    assert "attributes" in data
    assert "a_only" in data["attributes"]
    assert "b_only" in data["attributes"]
    assert "a_and_b" in data["attributes"]
    assert "array_elements" in data
    assert "a_count" in data["array_elements"]
    assert "b_count" in data["array_elements"]
    assert "a_and_b_count" in data["array_elements"]
    assert "a_and_b_same_order" in data["array_elements"]


def check_comparison_same_order_values(api_root):
    """Identical comparison: a_and_b_same_order values are all true."""
    digest = DIGEST_TESTS[0][1]["top_level_digest"]
    data = requests.get(
        f"{api_root}/comparison/{digest}/{digest}", timeout=COMPLIANCE_TIMEOUT
    ).json()
    same_order = data["array_elements"]["a_and_b_same_order"]
    for attr, val in same_order.items():
        assert val is True or val is False or val is None, (
            f"a_and_b_same_order[{attr}] must be bool or null, got {type(val)}"
        )
        assert val is True, f"Identical comparison: a_and_b_same_order[{attr}] should be true"


def check_comparison_post(api_root, fixture_name, expected):
    """POST comparison with local seqcol body returns correct diff."""
    import refget

    digest_b = expected["digests"]["b"]
    client = refget.SequenceCollectionClient(urls=[api_root])
    local_collection = client.get_collection(digest_b)

    digest_a = expected["digests"]["a"]
    res = requests.post(
        f"{api_root}/comparison/{digest_a}",
        json=local_collection,
        timeout=COMPLIANCE_TIMEOUT,
    )
    assert res.status_code == 200, (
        f"Comparison POST returned HTTP {res.status_code} for {fixture_name}"
    )
    data = res.json()
    assert data["digests"]["a"] == expected["digests"]["a"], (
        f"POST digest a: expected {expected['digests']['a']}, got {data['digests']['a']}"
    )
    assert data["attributes"] == expected["attributes"], (
        f"POST attributes for {fixture_name}: expected {expected['attributes']}, got {data['attributes']}"
    )
    assert data["array_elements"] == expected["array_elements"], (
        f"POST array_elements for {fixture_name}: expected {expected['array_elements']}, got {data['array_elements']}"
    )


# ============================================================
# Check registry -- builds the full compliance suite
# ============================================================


def build_checks(api_root: str) -> list[tuple[str, callable, list]]:
    """Build the complete list of compliance checks.

    Returns list of (name, function, args) tuples.
    """
    checks = []

    # Structure checks
    checks.append(("service_info", check_service_info, [api_root]))
    checks.append(("list_collections", check_list_collections, [api_root]))
    for attr in ["lengths", "names", "sequences"]:
        checks.append((f"list_attributes_{attr}", check_list_attributes, [api_root, attr]))
    checks.append(("openapi_available", check_openapi_available, [api_root]))

    # Collection content checks (per FASTA file)
    for fa_name, bundle in DIGEST_TESTS:
        tag = fa_name.replace(".fa", "")
        checks.append(
            (f"collection_level1_{tag}", check_collection_level1, [api_root, fa_name, bundle])
        )
        checks.append(
            (f"collection_level2_{tag}", check_collection_level2, [api_root, fa_name, bundle])
        )
        checks.append(
            (
                f"default_level2_{tag}",
                check_default_level_returns_level2,
                [api_root, fa_name, bundle],
            )
        )
        checks.append(
            (f"snlp_digest_{tag}", check_sorted_name_length_pairs, [api_root, fa_name, bundle])
        )

    # Attribute retrieval checks (per FASTA, per attribute)
    for fa_name, bundle in DIGEST_TESTS:
        tag = fa_name.replace(".fa", "")
        for attr in ["lengths", "names", "sequences"]:
            checks.append(
                (
                    f"attribute_{attr}_{tag}",
                    check_attribute_retrieval,
                    [api_root, fa_name, bundle, attr],
                )
            )

    # Attribute filtering checks
    checks.append(
        ("transient_attribute_not_served", check_transient_attribute_not_served, [api_root])
    )
    checks.append(
        ("multi_attribute_filter_and", check_list_multi_attribute_filter_and, [api_root])
    )

    # List filter checks (base.fa, filter by each attribute)
    base_name, base_bundle = DIGEST_TESTS[0]
    for attr in ["lengths", "names", "sequences"]:
        checks.append(
            (
                f"list_filter_{attr}",
                check_list_filter_by_attribute,
                [api_root, base_name, base_bundle, attr],
            )
        )

    # Comparison checks
    checks.append(("comparison_structure", check_comparison_structure, [api_root]))
    checks.append(("comparison_same_order", check_comparison_same_order_values, [api_root]))

    for fixture_name, expected in COMPARISON_FIXTURES.items():
        tag = fixture_name.replace("compare_", "").replace(".json", "")
        checks.append((f"comparison_{tag}", check_comparison, [api_root, fixture_name, expected]))
        checks.append(
            (f"comparison_post_{tag}", check_comparison_post, [api_root, fixture_name, expected])
        )

    return checks


# ============================================================
# Runners -- batch and streaming
# ============================================================


def run_compliance(api_root: str) -> dict:
    """Run all compliance checks and return a report dict."""
    api_root = api_root.rstrip("/")
    report = ComplianceReport(
        server_url=api_root,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )

    for name, func, args in build_checks(api_root):
        result = _timed_check(name, func, *args)
        report.results.append(asdict(result))
        report.total += 1
        if result.passed:
            report.passed += 1
        else:
            report.failed += 1

    return report.to_dict()


def run_compliance_stream(api_root: str):
    """Generator that yields each check result as a JSON string for SSE streaming."""
    api_root = api_root.rstrip("/")
    checks = build_checks(api_root)

    yield json.dumps({"type": "start", "total": len(checks), "server_url": api_root})

    passed = 0
    failed = 0
    for name, func, args in checks:
        result = _timed_check(name, func, *args)
        if result.passed:
            passed += 1
        else:
            failed += 1
        yield json.dumps({"type": "result", **asdict(result)})

    yield json.dumps({"type": "done", "passed": passed, "failed": failed, "total": len(checks)})
