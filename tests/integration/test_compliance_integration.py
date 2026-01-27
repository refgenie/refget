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
        # GA4GH service-info required fields
        assert "id" in data
        assert "type" in data
        assert "group" in data["type"]
        assert "artifact" in data["type"]
        assert "version" in data["type"]

    def test_service_info_seqcol_schema(self, test_server):
        """Service-info MUST include seqcol.schema (GA4GH spec requirement)"""
        res = requests.get(f"{test_server}/service-info")
        assert res.status_code == 200
        data = res.json()
        # Spec: service-info MUST return the JSON Schema implemented by the server
        assert "seqcol" in data, "service-info must have 'seqcol' section"
        assert "schema" in data["seqcol"], "seqcol section must include 'schema'"
        schema = data["seqcol"]["schema"]
        # Schema should define the required attributes
        assert "properties" in schema, "schema must have 'properties'"
        assert "lengths" in schema["properties"], "schema must define 'lengths'"
        assert "names" in schema["properties"], "schema must define 'names'"
        assert "sequences" in schema["properties"], "schema must define 'sequences'"

    def test_list_collections_structure(self, test_server):
        """List collections has pagination structure per GA4GH paging guide"""
        res = requests.get(f"{test_server}/list/collection")
        assert res.status_code == 200
        data = res.json()
        assert "results" in data
        assert isinstance(data["results"], list)
        assert "pagination" in data
        assert "page" in data["pagination"]
        assert "page_size" in data["pagination"]
        assert "total" in data["pagination"], "pagination must include 'total' per GA4GH spec"

    def test_list_collections_filter_by_attribute(self, test_server):
        """List collections filtered by attribute digest (REQUIRED by spec)"""
        # Use base.fa's names digest to filter
        names_digest = DIGEST_TESTS[0][1]["level1"]["names"]
        res = requests.get(f"{test_server}/list/collection?names={names_digest}")
        assert res.status_code == 200
        data = res.json()
        assert "results" in data
        # Should return only collections with this exact names digest
        # base.fa has this names digest
        assert DIGEST_TESTS[0][1]["top_level_digest"] in data["results"]


class TestAttributeEndpoint:
    """Test /attribute/collection/:attr/:digest endpoint (REQUIRED by spec)."""

    @pytest.mark.parametrize("fa_file, fa_digest_bundle", DIGEST_TESTS)
    def test_attribute_lengths(self, test_server, fa_file, fa_digest_bundle):
        """Retrieve lengths attribute by its digest"""
        lengths_digest = fa_digest_bundle["level1"]["lengths"]
        expected_lengths = fa_digest_bundle["level2"]["lengths"]
        res = requests.get(f"{test_server}/attribute/collection/lengths/{lengths_digest}")
        assert res.status_code == 200
        data = res.json()
        assert data == expected_lengths

    @pytest.mark.parametrize("fa_file, fa_digest_bundle", DIGEST_TESTS)
    def test_attribute_names(self, test_server, fa_file, fa_digest_bundle):
        """Retrieve names attribute by its digest"""
        names_digest = fa_digest_bundle["level1"]["names"]
        expected_names = fa_digest_bundle["level2"]["names"]
        res = requests.get(f"{test_server}/attribute/collection/names/{names_digest}")
        assert res.status_code == 200
        data = res.json()
        assert data == expected_names

    @pytest.mark.parametrize("fa_file, fa_digest_bundle", DIGEST_TESTS)
    def test_attribute_sequences(self, test_server, fa_file, fa_digest_bundle):
        """Retrieve sequences attribute by its digest"""
        sequences_digest = fa_digest_bundle["level1"]["sequences"]
        expected_sequences = fa_digest_bundle["level2"]["sequences"]
        res = requests.get(f"{test_server}/attribute/collection/sequences/{sequences_digest}")
        assert res.status_code == 200
        data = res.json()
        assert data == expected_sequences

    def test_attribute_not_found(self, test_server):
        """Non-existent attribute digest returns 404"""
        res = requests.get(f"{test_server}/attribute/collection/names/nonexistent_digest_12345")
        assert res.status_code == 404


class TestCollectionLevels:
    """Test collection level 1 vs level 2 response formats."""

    @pytest.mark.parametrize("fa_file, fa_digest_bundle", DIGEST_TESTS)
    def test_default_level_returns_level2(self, test_server, fa_file, fa_digest_bundle):
        """Collection without ?level= param returns level 2 (spec default)"""
        digest = fa_digest_bundle["top_level_digest"]
        res = requests.get(f"{test_server}/collection/{digest}")
        assert res.status_code == 200
        data = res.json()
        # Level 2 returns arrays, not digest strings
        for attr in ["names", "lengths", "sequences"]:
            assert isinstance(data[attr], list), f"Default should return level 2 (arrays)"

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
        assert (
            data["sorted_name_length_pairs"] == fa_digest_bundle["sorted_name_length_pairs_digest"]
        )


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

    def test_compare_full_structure(self, test_server):
        """Comparison returns complete structure per spec"""
        digest_a = DIGEST_TESTS[0][1]["top_level_digest"]  # base.fa
        digest_b = DIGEST_TESTS[1][1]["top_level_digest"]  # different_names.fa
        res = requests.get(f"{test_server}/comparison/{digest_a}/{digest_b}")
        assert res.status_code == 200
        data = res.json()
        # Verify digests structure
        assert "digests" in data
        assert "a" in data["digests"]
        assert "b" in data["digests"]
        # Verify attributes structure
        assert "attributes" in data
        assert "a_only" in data["attributes"]
        assert "b_only" in data["attributes"]
        assert "a_and_b" in data["attributes"]
        # Verify array_elements structure
        assert "array_elements" in data
        assert "a_count" in data["array_elements"]
        assert "b_count" in data["array_elements"]
        assert "a_and_b_count" in data["array_elements"]
        assert "a_and_b_same_order" in data["array_elements"]

    def test_compare_post_with_seqcol_body(self, test_server):
        """POST comparison with local seqcol in body (RECOMMENDED by spec)"""
        digest_a = DIGEST_TESTS[0][1]["top_level_digest"]  # base.fa on server
        # POST the level 2 representation of different_names.fa
        seqcol_b = DIGEST_TESTS[1][1]["level2"]
        res = requests.post(
            f"{test_server}/comparison/{digest_a}",
            json=seqcol_b,
        )
        assert res.status_code == 200
        data = res.json()
        assert "digests" in data
        assert data["digests"]["a"] == digest_a
        # b digest may be computed or null per spec
        assert "attributes" in data
        assert "array_elements" in data

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
