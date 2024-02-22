import pytest
import requests


def pytest_addoption(parser):
    """
    Add an option to specify the API root
    """
    parser.addoption("--api_root", action="store", default="http://0.0.0.0:8100")


@pytest.fixture()
def api_root(pytestconfig):
    """
    Get the API root from the command line argument, --api_root
    """
    return pytestconfig.getoption("api_root")


def check_server_is_running(api_root):
    """
    Check if a server is responding at the given API root
    """
    try:
        print(f"Checking if service is running at {api_root}")
        res = requests.get(f"{api_root}/")
        assert res.status_code == 200, "Service is not running"
        return True
    except:
        return False


REQ_SERVICE_MARK = "require_service"


def pytest_configure(config):
    """
    Register a custom marker for tests that require a server.
    You can add this marker to a test with `@pytest.mark.require_service`,
    and it will be skipped if the server is not running.
    """
    config.addinivalue_line(
        "markers", f"{REQ_SERVICE_MARK}: test to only run when API root is available"
    )


def pytest_collection_modifyitems(config, items):
    """
    Skip tests marked with `@pytest.mark.require_service` if the server is not running
    """
    api_root = config.getoption("api_root")
    skip_missing_service = pytest.mark.skip(reason="need API to run")
    if not check_server_is_running(api_root):
        print("Skipping tests that require a server to be running...")
        for item in items:
            if REQ_SERVICE_MARK in item.keywords:
                item.add_marker(skip_missing_service)
