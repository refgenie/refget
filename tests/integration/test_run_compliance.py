"""Run the standalone compliance suite against the integration test server."""

import pytest

from tests.api.test_compliance import TestAPI


@pytest.mark.require_service
class TestComplianceViaIntegration(TestAPI):
    """Run compliance tests against integration test server.

    Inherits all tests from TestAPI but provides api_root from
    the integration test_server fixture instead of --api-root CLI option.
    """

    @pytest.fixture
    def api_root(self, test_server):
        """Map test_server fixture to api_root for compliance tests."""
        return test_server
