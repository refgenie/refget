"""Run the compliance suite against a store-backed seqcolapi server."""

import pytest

import refget.compliance as compliance
from tests.api.test_compliance import TestAPI

# Load test data at import time — tests always run from the repo
compliance._load_test_data()


@pytest.mark.require_service
class TestStoreCompliance(TestAPI):
    """Run compliance tests against store-backed seqcolapi server.

    Inherits all tests from TestAPI but provides api_root from
    the store_test_server fixture. The store backend implements the full
    SeqColBackend protocol, so every compliance test applies unmodified.
    """

    @pytest.fixture
    def api_root(self, store_test_server):
        return store_test_server
