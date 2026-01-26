"""
Compliance tests running against the integration test server.

These tests verify the API responses match expected fixtures,
using the ephemeral Docker PostgreSQL + test server infrastructure.
"""

import json
import pytest
import requests
from pathlib import Path

from tests.conftest import DIGEST_TESTS


class TestComplianceStructure:
    """Test response structure matches GA4GH spec."""

    def test_service_info_structure(self, test_server):
        """Service-info has required GA4GH fields"""
        res = requests.get(f"{test_server}/service-info")
        assert res.status_code == 200
        data = res.json()
        assert "id" in data
        assert "type" in data
        assert "group" in data["type"]
        assert "artifact" in data["type"]
        assert "version" in data["type"]

    def test_list_collections_structure(self, test_server):
        """List collections has pagination structure"""
        res = requests.get(f"{test_server}/list/collection")
        assert res.status_code == 200
        data = res.json()
        assert "results" in data
        assert isinstance(data["results"], list)
        assert "pagination" in data
        assert "page" in data["pagination"]
        assert "page_size" in data["pagination"]

    @pytest.mark.parametrize("attribute_name", ["lengths", "names", "sequences"])
    def test_list_attributes_structure(self, test_server, attribute_name):
        """List attributes has pagination structure"""
        res = requests.get(f"{test_server}/list/attributes/{attribute_name}")
        assert res.status_code == 200
        data = res.json()
        assert "results" in data
        assert isinstance(data["results"], list)


class TestCollectionLevels:
    """Test collection level 1 vs level 2 response formats."""

    @pytest.mark.parametrize("fa_file, fa_digest_bundle", DIGEST_TESTS)
    def test_level1_returns_digests(self, test_server, fa_file, fa_digest_bundle):
        """Level 1 returns digest strings for attributes"""
        digest = fa_digest_bundle["top_level_digest"]
        res = requests.get(f"{test_server}/collection/{digest}?level=1")
        assert res.status_code == 200
        data = res.json()
        for attr in ["names", "lengths", "sequences"]:
            assert isinstance(data[attr], str), f"Level 1 {attr} should be digest string"
        # Transient attribute present in level 1
        assert "sorted_name_length_pairs" in data

    @pytest.mark.parametrize("fa_file, fa_digest_bundle", DIGEST_TESTS)
    def test_level2_returns_arrays(self, test_server, fa_file, fa_digest_bundle):
        """Level 2 returns arrays for attributes"""
        digest = fa_digest_bundle["top_level_digest"]
        res = requests.get(f"{test_server}/collection/{digest}?level=2")
        assert res.status_code == 200
        data = res.json()
        for attr in ["names", "lengths", "sequences"]:
            assert isinstance(data[attr], list), f"Level 2 {attr} should be array"
        # Transient attribute NOT in level 2
        assert "sorted_name_length_pairs" not in data

    @pytest.mark.parametrize("fa_file, fa_digest_bundle", DIGEST_TESTS)
    def test_sorted_name_length_pairs_digest(self, test_server, fa_file, fa_digest_bundle):
        """Level 1 sorted_name_length_pairs matches expected digest"""
        digest = fa_digest_bundle["top_level_digest"]
        res = requests.get(f"{test_server}/collection/{digest}?level=1")
        assert res.status_code == 200
        data = res.json()
        assert data["sorted_name_length_pairs"] == fa_digest_bundle["sorted_name_length_pairs_digest"]


class TestComparison:
    """Test comparison endpoint responses."""

    def test_compare_identical(self, test_server):
        """Comparing collection to itself returns expected structure"""
        # Use base.fa digest
        digest = DIGEST_TESTS[0][1]["top_level_digest"]
        res = requests.get(f"{test_server}/comparison/{digest}/{digest}")
        assert res.status_code == 200
        data = res.json()
        assert "digests" in data
        assert data["digests"]["a"] == digest
        assert data["digests"]["b"] == digest
        assert "attributes" in data
        assert "array_elements" in data

    def test_compare_different(self, test_server):
        """Comparing different collections returns diff structure"""
        digest_a = DIGEST_TESTS[0][1]["top_level_digest"]  # base.fa
        digest_b = DIGEST_TESTS[1][1]["top_level_digest"]  # different_names.fa
        res = requests.get(f"{test_server}/comparison/{digest_a}/{digest_b}")
        assert res.status_code == 200
        data = res.json()
        assert data["digests"]["a"] == digest_a
        assert data["digests"]["b"] == digest_b
        assert "a_and_b" in data["attributes"]

    def test_compare_with_fixtures(self, test_server):
        """Comparison results match fixture files"""
        # Test base.fa vs different_names.fa comparison
        with open("tests/api/comparison/compare_base.fa_different_names.fa.json") as f:
            expected = json.load(f)

        res = requests.get(
            f"{test_server}/comparison/{expected['digests']['a']}/{expected['digests']['b']}"
        )
        assert res.status_code == 200
        data = res.json()
        assert data["digests"] == expected["digests"]
        assert data["attributes"] == expected["attributes"]
        assert data["array_elements"] == expected["array_elements"]


class TestCollectionContent:
    """Test collection content matches fixtures."""

    @pytest.mark.parametrize("fa_file, fa_digest_bundle", DIGEST_TESTS)
    def test_collection_content(self, test_server, fa_file, fa_digest_bundle):
        """Collection arrays match expected values from digests file"""
        digest = fa_digest_bundle["top_level_digest"]
        expected = fa_digest_bundle["level2"]
        res = requests.get(f"{test_server}/collection/{digest}?level=2")
        assert res.status_code == 200
        data = res.json()

        # Verify lengths match
        assert data["lengths"] == expected["lengths"]
        # Verify names match
        assert data["names"] == expected["names"]
        # Verify sequence digests match
        assert data["sequences"] == expected["sequences"]
