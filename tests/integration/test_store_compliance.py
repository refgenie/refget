"""Run the compliance suite against a store-backed seqcolapi server."""

import pytest
import requests

import refget.compliance as compliance
from refget.compliance import COMPLIANCE_TIMEOUT, check_transient_attribute_not_served
from tests.api.test_compliance import TestAPI

# Load test data at import time — tests always run from the repo
compliance._load_test_data()
DIGEST_TESTS = compliance.DIGEST_TESTS
COMPARISON_FIXTURES = compliance.COMPARISON_FIXTURES


@pytest.mark.require_service
class TestStoreCompliance(TestAPI):
    """Run compliance tests against store-backed seqcolapi server.

    Inherits all tests from TestAPI but provides api_root from
    the store_test_server fixture. DB-only endpoints are overridden
    to assert the expected non-200 behavior.
    """

    @pytest.fixture
    def api_root(self, store_test_server):
        return store_test_server

    # --- Override DB-only tests ---

    @pytest.mark.parametrize("attribute_name", ["lengths", "names", "sequences"])
    def test_list_attributes(self, api_root, attribute_name):
        """Store backend: /list/attributes returns 501 (DB-only endpoint)."""
        res = requests.get(
            f"{api_root}/list/attributes/{attribute_name}",
            timeout=COMPLIANCE_TIMEOUT,
        )
        assert res.status_code == 501

    @pytest.mark.parametrize("attr_name", ["lengths", "names", "sequences"])
    def test_list_filter_by_attribute(self, api_root, attr_name):
        """Store backend: attribute filtering returns 400 (not supported)."""
        fa_name, bundle = DIGEST_TESTS[0]
        attr_digest = bundle["level1"][attr_name]
        res = requests.get(
            f"{api_root}/list/collection?{attr_name}={attr_digest}",
            timeout=COMPLIANCE_TIMEOUT,
        )
        assert res.status_code == 400

    def test_multi_attribute_filter_and(self, api_root):
        """Store backend: multi-attribute filtering returns 400 (not supported)."""
        bundle = DIGEST_TESTS[0][1]
        res = requests.get(
            f"{api_root}/list/collection?names={bundle['level1']['names']}&lengths={bundle['level1']['lengths']}",
            timeout=COMPLIANCE_TIMEOUT,
        )
        assert res.status_code == 400

    def test_transient_attribute_not_served(self, api_root):
        """Transient attributes should return 404 from /attribute endpoint."""
        check_transient_attribute_not_served(api_root)
