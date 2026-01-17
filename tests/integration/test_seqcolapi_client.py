"""
SeqCol API Integration Tests

Tests API endpoints using FastAPI TestClient with ephemeral Docker PostgreSQL.

Prerequisites:
1. Start test database: ./tests/integration/scripts/test-db.sh start
2. Run tests: RUN_INTEGRATION_TESTS=true pytest tests/integration/
"""
import os
import pytest

# Skip all tests in this module unless RUN_INTEGRATION_TESTS=true
pytestmark = pytest.mark.skipif(
    os.getenv("RUN_INTEGRATION_TESTS") != "true",
    reason="Integration tests disabled. Set RUN_INTEGRATION_TESTS=true to run.",
)


class TestServiceAvailability:
    """Verify the API is responding"""

    def test_root_endpoint(self, client):
        """Root endpoint should return 200"""
        response = client.get("/")
        assert response.status_code == 200

    def test_service_info(self, client):
        """Service-info endpoint should return valid response"""
        response = client.get("/service-info")
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "name" in data
        assert "type" in data


class TestSequenceCollectionEndpoints:
    """Test sequence collection API endpoints"""

    def test_get_collection(self, client, base_digest):
        """GET /collection/{digest} should return collection"""
        response = client.get(f"/collection/{base_digest}")
        assert response.status_code == 200
        data = response.json()
        assert "names" in data
        assert "lengths" in data
        assert "sequences" in data

    def test_get_collection_level1(self, client, base_digest):
        """GET /collection/{digest}?level=1 should return level1 digests"""
        response = client.get(f"/collection/{base_digest}?level=1")
        assert response.status_code == 200
        data = response.json()
        # Level 1 returns digests, not arrays
        assert "names" in data
        assert isinstance(data["names"], str)

    def test_get_collection_not_found(self, client):
        """GET /collection/{invalid} should return 404"""
        response = client.get("/collection/INVALID_DIGEST_12345")
        assert response.status_code == 404

    def test_list_collections(self, client):
        """GET /list/collection should return paginated results"""
        response = client.get("/list/collection")
        assert response.status_code == 200
        data = response.json()
        assert "pagination" in data
        assert "results" in data
        assert len(data["results"]) >= 3  # We loaded 3 test files

    def test_list_collections_with_pagination(self, client):
        """GET /list/collection with pagination params"""
        response = client.get("/list/collection?page_size=2&page=0")
        assert response.status_code == 200
        data = response.json()
        assert data["pagination"]["page_size"] == 2

    def test_list_attributes(self, client):
        """GET /list/attributes/{attribute} should return attribute values"""
        response = client.get("/list/attributes/lengths")
        assert response.status_code == 200
        data = response.json()
        assert "pagination" in data
        assert "results" in data


class TestComparisonEndpoints:
    """Test sequence collection comparison endpoints"""

    def test_compare_two_collections(self, client, base_digest, different_order_digest):
        """GET /comparison/{d1}/{d2} should return comparison"""
        response = client.get(f"/comparison/{base_digest}/{different_order_digest}")
        assert response.status_code == 200
        data = response.json()
        assert "digests" in data
        assert data["digests"]["a"] == base_digest
        assert data["digests"]["b"] == different_order_digest
        assert "array_elements" in data

    def test_compare_same_collection(self, client, base_digest):
        """Comparing collection to itself should show perfect match"""
        response = client.get(f"/comparison/{base_digest}/{base_digest}")
        assert response.status_code == 200
        data = response.json()
        assert "digests" in data
        assert "array_elements" in data
        # Same collection should have equal counts
        assert data["array_elements"]["a_count"] == data["array_elements"]["b_count"]

    def test_compare_with_local(self, client, base_digest):
        """POST /comparison/{d1} with local collection"""
        local_collection = {
            "names": ["chrX", "chr1", "chr2"],
            "lengths": [8, 4, 4],
            "sequences": [
                "SQ.iYtREV555dUFKg2_agSJW6suquUyPpMw",
                "SQ.YBbVX0dLKG1ieEDCiMmkrTZFt_Z5Vdaj",
                "SQ.AcLxtBuKEPk_7PGE_H4dGElwZHCujwH6",
            ],
        }
        response = client.post(f"/comparison/{base_digest}", json=local_collection)
        assert response.status_code == 200
        data = response.json()
        assert "digests" in data


class TestFastaDrsEndpoints:
    """Test FASTA DRS endpoints"""

    def test_drs_service_info(self, client):
        """GET /fasta/service-info should return DRS service info"""
        response = client.get("/fasta/service-info")
        assert response.status_code == 200
        data = response.json()
        assert data["type"]["artifact"] == "drs"

    def test_get_drs_object(self, client, base_digest):
        """GET /fasta/objects/{id} should return DRS object"""
        response = client.get(f"/fasta/objects/{base_digest}")
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["id"] == base_digest

    def test_get_drs_object_not_found(self, client):
        """GET /fasta/objects/{invalid} should return 404"""
        response = client.get("/fasta/objects/INVALID_DIGEST")
        assert response.status_code == 404

    def test_get_fasta_index(self, client, base_digest):
        """GET /fasta/objects/{id}/index should return FAI index data"""
        response = client.get(f"/fasta/objects/{base_digest}/index")
        assert response.status_code == 200
        data = response.json()
        assert "line_bases" in data
        assert "extra_line_bytes" in data
        assert "offsets" in data
