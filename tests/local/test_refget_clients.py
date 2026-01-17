"""
Unit tests for refget client classes.

These tests verify client construction and basic functionality
without requiring a running server.

For integration tests that test against a real API,
see tests/integration/test_seqcolapi_client.py
"""
from refget import SequenceCollectionClient, FastaDrsClient


class TestClientConstruction:
    """Test client class construction"""

    def test_seqcol_client_default_urls(self):
        """SequenceCollectionClient can be created with default URLs"""
        client = SequenceCollectionClient()
        assert isinstance(client, SequenceCollectionClient)
        assert len(client.urls) > 0

    def test_seqcol_client_custom_urls(self):
        """SequenceCollectionClient accepts custom URLs"""
        client = SequenceCollectionClient(urls=["https://example.com"])
        assert isinstance(client, SequenceCollectionClient)
        assert client.urls == ["https://example.com"]

    def test_seqcol_client_strips_trailing_slashes(self):
        """SequenceCollectionClient strips trailing slashes from URLs"""
        client = SequenceCollectionClient(urls=["https://example.com/"])
        assert client.urls == ["https://example.com"]

    def test_fasta_drs_client_default_urls(self):
        """FastaDrsClient can be created with default URLs"""
        client = FastaDrsClient()
        assert isinstance(client, FastaDrsClient)
        assert len(client.urls) > 0

    def test_fasta_drs_client_custom_urls(self):
        """FastaDrsClient accepts custom URLs"""
        client = FastaDrsClient(urls=["https://example.com/fasta"])
        assert isinstance(client, FastaDrsClient)
        assert client.urls == ["https://example.com/fasta"]
