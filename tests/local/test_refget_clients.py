"""
Unit tests for refget client classes.

These tests verify client construction and basic functionality
without requiring a running server.

For integration tests that test against a real API,
see tests/integration/test_seqcolapi_client.py
"""

import pytest

from refget.clients import FastaDrsClient, SequenceCollectionClient


class TestClientConstruction:
    """Test client class construction"""

    @pytest.mark.parametrize(
        "cls,kwargs,expected_url_count",
        [
            (SequenceCollectionClient, {}, None),  # default URLs, just check > 0
            (SequenceCollectionClient, {"urls": ["https://example.com"]}, 1),
            (FastaDrsClient, {}, None),
            (FastaDrsClient, {"urls": ["https://example.com/fasta"]}, 1),
        ],
    )
    def test_client_construction(self, cls, kwargs, expected_url_count):
        client = cls(**kwargs)
        assert isinstance(client, cls)
        if expected_url_count is not None:
            assert len(client.urls) == expected_url_count
        else:
            assert len(client.urls) > 0

    def test_seqcol_client_strips_trailing_slashes(self):
        """SequenceCollectionClient strips trailing slashes from URLs"""
        client = SequenceCollectionClient(urls=["https://example.com/"])
        assert client.urls == ["https://example.com"]
