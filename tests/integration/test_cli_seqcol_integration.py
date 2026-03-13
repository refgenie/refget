# tests/integration/test_cli_seqcol_integration.py

"""
Integration tests for refget seqcol CLI commands that require a server.

Run with: ./scripts/test-integration.sh
"""

import json


class TestSeqcolShow:
    """Tests for: refget seqcol show <digest>"""

    def test_show_known_digest(self, cli_runner, test_server, base_digest):
        """Shows seqcol for known digest from test server."""
        result = cli_runner("seqcol", "show", base_digest, "--server", test_server)

        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert "names" in data
        assert "lengths" in data
        assert "sequences" in data

    def test_show_level_1(self, cli_runner, test_server, base_digest):
        """Shows digest at level 1 (digests only)."""
        result = cli_runner("seqcol", "show", base_digest, "--server", test_server, "--level", "1")

        assert result.exit_code == 0
        data = json.loads(result.stdout)
        # Level 1 should have string digests, not arrays
        assert isinstance(data.get("names"), str)
        assert isinstance(data.get("lengths"), str)

    def test_show_nonexistent_digest(self, cli_runner, test_server):
        """Show of nonexistent digest returns error."""
        result = cli_runner(
            "seqcol", "show", "nonexistent_digest_that_does_not_exist", "--server", test_server
        )

        assert result.exit_code != 0


class TestSeqcolList:
    """Tests for: refget seqcol list"""

    def test_list_collections(self, cli_runner, test_server):
        """Lists collections from server."""
        result = cli_runner("seqcol", "list", "--server", test_server)

        assert result.exit_code == 0
        data = json.loads(result.stdout)
        # Should have results array or items
        assert "results" in data or "items" in data or isinstance(data, list)

    def test_list_with_limit(self, cli_runner, test_server):
        """Lists collections with limit."""
        result = cli_runner("seqcol", "list", "--server", test_server, "--limit", "2")

        assert result.exit_code == 0


class TestSeqcolSearch:
    """Tests for: refget seqcol search"""

    def test_search_by_names_digest(self, cli_runner, test_server, client, base_digest):
        """Searches for collections by names digest."""
        # First, get the names digest from the collection
        response = client.get(f"/collection/{base_digest}?level=1")
        assert response.status_code == 200
        level1_data = response.json()
        names_digest = level1_data.get("names")

        if names_digest:
            result = cli_runner(
                "seqcol", "search", "--names", names_digest, "--server", test_server
            )

            assert result.exit_code == 0


class TestSeqcolAttribute:
    """Tests for: refget seqcol attribute"""

    def test_get_attribute(self, cli_runner, test_server, client, base_digest):
        """Gets attribute array by digest."""
        # First, get the names digest from the collection
        response = client.get(f"/collection/{base_digest}?level=1")
        assert response.status_code == 200
        level1_data = response.json()
        names_digest = level1_data.get("names")

        if names_digest:
            result = cli_runner(
                "seqcol",
                "attribute",
                names_digest,
                "--attribute",
                "names",
                "--server",
                test_server,
            )

            assert result.exit_code == 0
            data = json.loads(result.stdout)
            assert isinstance(data, list)


class TestSeqcolInfo:
    """Tests for: refget seqcol info"""

    def test_get_server_info(self, cli_runner, test_server):
        """Gets server info/capabilities."""
        result = cli_runner("seqcol", "info", "--server", test_server)

        assert result.exit_code == 0
        data = json.loads(result.stdout)
        # Should have service info
        assert isinstance(data, dict)


class TestSeqcolCompareRemote:
    """Tests for comparing with remote digests."""

    def test_compare_local_to_remote(self, cli_runner, test_server, test_fasta_path, base_digest):
        """Compare local FASTA with remote digest."""
        fasta_path = test_fasta_path / "base.fa"

        result = cli_runner(
            "seqcol", "compare", str(fasta_path), base_digest, "--server", test_server
        )

        assert result.exit_code == 0
        data = json.loads(result.stdout)
        # Should show identical match
        assert data.get("compatible", False) is True

    def test_compare_two_remote_digests(
        self, cli_runner, test_server, base_digest, different_order_digest
    ):
        """Compare two remote digests."""
        result = cli_runner(
            "seqcol", "compare", base_digest, different_order_digest, "--server", test_server
        )

        # The command should complete (stdout has JSON)
        data = json.loads(result.stdout)
        assert isinstance(data, dict)
        assert "compatible" in data
        assert "attributes" in data
        assert "array_elements" in data

        # base.fa and different_order.fa ARE compatible (same coordinate system)
        # They have the same sequences, names, and lengths - just different order
        # Compatibility is based on sorted_name_length_pairs matching (same coord system)
        assert data["compatible"] is True
        assert result.exit_code == 0


class TestSeqcolServers:
    """Tests for: refget seqcol servers"""

    def test_list_servers(self, cli_runner):
        """Lists configured seqcol servers."""
        result = cli_runner("seqcol", "servers")

        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert "servers" in data
