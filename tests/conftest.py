""" Test suite shared objects and setup """
import os
import pytest
import oyaml as yaml
from seqcol.const import _schema_path


def ly(n, data_path):
    """Load YAML"""
    with open(os.path.join(data_path, n), "r") as f:
        return yaml.safe_load(f)


@pytest.fixture
def schema_path():
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "schemas")


@pytest.fixture
def fa_root():
    return os.path.join(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir),
        "demo_fasta",
    )

@pytest.fixture
def fasta_path():
    return os.path.join(os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir), "demo_fasta")


@pytest.fixture
def schema_sequence(schema_path):
    return ly("sequence.yaml", schema_path)


@pytest.fixture
def schema_asd(schema_path):
    return ly("annotated_sequence_digest.yaml", schema_path)


@pytest.fixture
def schema_acd(schema_path):
    return ly("annotated_collection_digest.yaml", schema_path)
