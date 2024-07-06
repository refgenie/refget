import pytest
import requests

from tests.conftest import DEMO_FILES

REQ_SERVICE_MARK = "require_service"
API_TEST_DIR = "test_api"

COLLECTION_TESTS = [
    (DEMO_FILES[0], f"{API_TEST_DIR}/collection/base_collection.json"),
    (DEMO_FILES[1], f"{API_TEST_DIR}/collection/different_names_collection.json"),
    (DEMO_FILES[2], f"{API_TEST_DIR}/collection/different_order_collection.json"),
    (DEMO_FILES[3], f"{API_TEST_DIR}/collection/pair_swap_collection.json"),
    (DEMO_FILES[4], f"{API_TEST_DIR}/collection/subset_collection.json"),
    (DEMO_FILES[5], f"{API_TEST_DIR}/collection/swap_wo_coords_collection.json"),
]

COMPARISON_TESTS = [
    f"{API_TEST_DIR}/comparison/compare_subset.json",  # subset
    f"{API_TEST_DIR}/comparison/compare_different_names.json",  # same sequences, different names
    f"{API_TEST_DIR}/comparison/compare_different_order.json",  # same sequences, name order switch, but equivalent coordinate system
    f"{API_TEST_DIR}/comparison/compare_pair_swap.json",  # swapped name-length-pairs
    f"{API_TEST_DIR}/comparison/compare_swap_wo_coords.json",  # swapped name-length-pairs, but no coord system change
]

ATTRIBUTE_TESTS = [
    ("lengths", "7-_HdxYiRf-AJLBKOTaJUdxXrUkIXs6T", [8,4]),
    ("names", "Fw1r9eRxfOZD98KKrhlYQNEdSRHoVxAG", ["chrX","chr1","chr2"])
]

ATTRIBUTE_LIST_TESTS = [
    ("lengths", "cGRMZIb3AVgkcAfNv39RN7hnT5Chk7RX", f"{API_TEST_DIR}/attribute/cGRM.json",)
]


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
        print("Server is running.")
        return True
    except:
        print("Server is not running.")
        return False




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
