import pytest
from pathlib import Path


@pytest.fixture(scope="session")
def test_data_root():
    """Provides the absolute path to the test_fasta directory."""
    current_dir = Path(__file__).parent.parent
    return current_dir.parent / "test_fasta"
