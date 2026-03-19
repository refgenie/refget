# Pytest wrapper for the GA4GH SeqCol compliance suite.
#
# The canonical compliance checks live in refget/compliance.py.
# This file parametrizes them for pytest execution.
#
# Run against an external server:
#   pytest tests/api --api-root https://seqcolapi.databio.org
#
# Run via integration test server:
#   ./scripts/test-integration.sh

import pytest

import refget.compliance as compliance
from refget.compliance import (
    check_attribute_retrieval,
    check_collection_level1,
    check_collection_level2,
    check_comparison,
    check_comparison_post,
    check_comparison_same_order_values,
    check_comparison_structure,
    check_default_level_returns_level2,
    check_list_attributes,
    check_list_collections,
    check_list_filter_by_attribute,
    check_list_multi_attribute_filter_and,
    check_openapi_available,
    check_service_info,
    check_sorted_name_length_pairs,
    check_transient_attribute_not_served,
)

# Load test data at import time — tests always run from the repo
compliance._load_test_data()
DIGEST_TESTS = compliance.DIGEST_TESTS
COMPARISON_FIXTURES = compliance.COMPARISON_FIXTURES


@pytest.mark.require_service
class TestAPI:
    """GA4GH SeqCol compliance tests. Expects demo data loaded on the server."""

    # ---- Structure checks ----

    def test_service_info(self, api_root):
        check_service_info(api_root)

    def test_list_collections(self, api_root):
        check_list_collections(api_root)

    @pytest.mark.parametrize("attribute_name", ["lengths", "names", "sequences"])
    def test_list_attributes(self, api_root, attribute_name):
        check_list_attributes(api_root, attribute_name)

    @pytest.mark.recommended
    def test_openapi_available(self, api_root):
        check_openapi_available(api_root)

    # ---- Collection content checks ----

    @pytest.mark.parametrize("fa_name, bundle", DIGEST_TESTS)
    def test_collection_level1(self, api_root, fa_name, bundle):
        check_collection_level1(api_root, fa_name, bundle)

    @pytest.mark.parametrize("fa_name, bundle", DIGEST_TESTS)
    def test_collection_level2(self, api_root, fa_name, bundle):
        check_collection_level2(api_root, fa_name, bundle)

    @pytest.mark.parametrize("fa_name, bundle", DIGEST_TESTS)
    def test_default_level_returns_level2(self, api_root, fa_name, bundle):
        check_default_level_returns_level2(api_root, fa_name, bundle)

    @pytest.mark.parametrize("fa_name, bundle", DIGEST_TESTS)
    def test_sorted_name_length_pairs(self, api_root, fa_name, bundle):
        check_sorted_name_length_pairs(api_root, fa_name, bundle)

    # ---- Attribute checks ----

    @pytest.mark.parametrize("fa_name, bundle", DIGEST_TESTS)
    @pytest.mark.parametrize("attr_name", ["lengths", "names", "sequences"])
    def test_attribute_retrieval(self, api_root, fa_name, bundle, attr_name):
        check_attribute_retrieval(api_root, fa_name, bundle, attr_name)

    def test_transient_attribute_not_served(self, api_root):
        check_transient_attribute_not_served(api_root)

    # ---- List/filter checks ----

    @pytest.mark.parametrize("attr_name", ["lengths", "names", "sequences"])
    def test_list_filter_by_attribute(self, api_root, attr_name):
        fa_name, bundle = DIGEST_TESTS[0]
        check_list_filter_by_attribute(api_root, fa_name, bundle, attr_name)

    def test_multi_attribute_filter_and(self, api_root):
        check_list_multi_attribute_filter_and(api_root)

    # ---- Comparison checks ----

    def test_comparison_structure(self, api_root):
        check_comparison_structure(api_root)

    def test_comparison_same_order_values(self, api_root):
        check_comparison_same_order_values(api_root)

    @pytest.mark.parametrize(
        "fixture_name, expected",
        list(COMPARISON_FIXTURES.items()),
        ids=list(COMPARISON_FIXTURES.keys()),
    )
    def test_comparison(self, api_root, fixture_name, expected):
        check_comparison(api_root, fixture_name, expected)

    @pytest.mark.parametrize(
        "fixture_name, expected",
        list(COMPARISON_FIXTURES.items()),
        ids=list(COMPARISON_FIXTURES.keys()),
    )
    def test_comparison_post(self, api_root, fixture_name, expected):
        check_comparison_post(api_root, fixture_name, expected)
