import pytest

def pytest_addoption(parser):
    parser.addoption("--api_root", action="store", default="http://0.0.0.0:8100")

@pytest.fixture()
def api_root(pytestconfig):
    return pytestconfig.getoption("api_root")