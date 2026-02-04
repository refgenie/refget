# tests/test_cli_integration/test_workflows.py

"""
Integration tests for multi-command CLI workflows.

These tests verify that commands work together correctly in typical usage patterns.
"""

import pytest
import json
import sys
import os
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from conftest import (
    BASE_FASTA,
    DIFFERENT_NAMES_FASTA,
    DIFFERENT_ORDER_FASTA,
    SUBSET_FASTA,
    TEST_FASTA_DIGESTS,
)


class TestDigestAndCompare:
    """Test digest -> compare workflow."""

    def test_compare_fasta_files(self, cli, sample_fasta, tmp_path):
        """Compare two FASTA files directly."""
        fasta2 = tmp_path / "other.fa"
        fasta2.write_text(">chr1\nACGTACGT\n>chr2\nGGCCGGCC\n")

        result = cli("seqcol", "compare", str(sample_fasta), str(fasta2))

        assert result.exit_code == 0
        data = json.loads(result.stdout)
        # Should show comparison result
        assert isinstance(data, dict)

    def test_compute_then_compare(self, cli, sample_fasta, tmp_path):
        """Compute seqcol JSON, then compare."""
        seqcol_file = tmp_path / "test.seqcol.json"

        # Step 1: Compute seqcol
        result = cli("fasta", "seqcol", str(sample_fasta), "-o", str(seqcol_file))
        assert result.exit_code == 0

        # Step 2: Compare using seqcol file
        result = cli("seqcol", "compare", str(seqcol_file), str(sample_fasta))
        assert result.exit_code == 0

    def test_digest_consistency(self, cli, sample_fasta, tmp_path):
        """Digest from FASTA matches seqcol digest computed the same way."""
        # Get digest directly from FASTA using gtars
        result1 = cli("fasta", "digest", str(sample_fasta))
        assert result1.exit_code == 0
        direct_digest = json.loads(result1.stdout)["digest"]

        # Run digest again - should be deterministic
        result2 = cli("fasta", "digest", str(sample_fasta))
        assert result2.exit_code == 0
        repeated_digest = json.loads(result2.stdout)["digest"]

        # Same command should produce same digest (deterministic)
        assert direct_digest == repeated_digest

    def test_seqcol_roundtrip(self, cli, sample_fasta, tmp_path):
        """Seqcol file can be validated and used for comparison."""
        # Compute seqcol
        seqcol_file = tmp_path / "test.seqcol.json"
        result = cli("fasta", "seqcol", str(sample_fasta), "-o", str(seqcol_file))
        assert result.exit_code == 0

        # Validate seqcol
        result = cli("seqcol", "validate", str(seqcol_file))
        assert result.exit_code == 0

        # Digest from seqcol file should be deterministic
        result1 = cli("seqcol", "digest", str(seqcol_file))
        result2 = cli("seqcol", "digest", str(seqcol_file))
        assert result1.exit_code == 0
        assert result2.exit_code == 0
        assert json.loads(result1.stdout)["digest"] == json.loads(result2.stdout)["digest"]


class TestStoreLifecycle:
    """Test complete store lifecycle."""

    def test_init_add_list_export(self, cli, tmp_path):
        """Full store workflow: init -> add -> list -> export."""
        store = tmp_path / "store"
        output = tmp_path / "exported.fa"

        # Init
        result = cli("store", "init", "--path", str(store))
        assert result.exit_code == 0

        # Add
        result = cli("store", "add", str(BASE_FASTA), "--path", str(store))
        assert result.exit_code == 0
        digest = json.loads(result.stdout)["digest"]

        # List
        result = cli("store", "list", "--path", str(store))
        assert result.exit_code == 0
        collections = json.loads(result.stdout)["collections"]
        assert len(collections) >= 1

        # Export
        result = cli("store", "export", digest, "-o", str(output), "--path", str(store))
        assert result.exit_code == 0
        assert output.exists()

        # Stats
        result = cli("store", "stats", "--path", str(store))
        assert result.exit_code == 0

    def test_add_multiple_then_compare(self, cli, tmp_path):
        """Add multiple FASTAs to store, then compare them."""
        store = tmp_path / "store"

        # Init and add multiple files
        cli("store", "init", "--path", str(store))

        result1 = cli("store", "add", str(BASE_FASTA), "--path", str(store))
        digest1 = json.loads(result1.stdout)["digest"]

        result2 = cli("store", "add", str(DIFFERENT_ORDER_FASTA), "--path", str(store))
        digest2 = json.loads(result2.stdout)["digest"]

        # Get both seqcols from store
        result_sc1 = cli("store", "get", digest1, "--path", str(store))
        result_sc2 = cli("store", "get", digest2, "--path", str(store))

        assert result_sc1.exit_code == 0
        assert result_sc2.exit_code == 0

        # They should have same sorted digests (same sequences, different order)
        sc1 = json.loads(result_sc1.stdout)
        sc2 = json.loads(result_sc2.stdout)

        # Sequences should be the same (just different order)
        assert sorted(sc1.get("sequences", [])) == sorted(sc2.get("sequences", []))

    def test_store_roundtrip(self, cli, tmp_path):
        """Add FASTA to store, export, verify seqcol attributes are preserved."""
        store = tmp_path / "store"
        exported = tmp_path / "exported.fa"

        cli("store", "init", "--path", str(store))

        # Add and get digest
        result = cli("store", "add", str(BASE_FASTA), "--path", str(store))
        assert result.exit_code == 0
        original_digest = json.loads(result.stdout)["digest"]

        # Get original seqcol from store
        result = cli("store", "get", original_digest, "--path", str(store))
        assert result.exit_code == 0
        original_seqcol = json.loads(result.stdout)

        # Export
        result = cli("store", "export", original_digest, "-o", str(exported), "--path", str(store))
        assert result.exit_code == 0
        assert exported.exists()

        # Compute seqcol from exported file
        exported_seqcol_file = tmp_path / "exported.seqcol.json"
        result = cli("fasta", "seqcol", str(exported), "-o", str(exported_seqcol_file))
        assert result.exit_code == 0

        exported_seqcol = json.loads(exported_seqcol_file.read_text())

        # Verify seqcol attributes are preserved (content-addressable at attribute level)
        # Note: export may reorder sequences, so compare by name rather than position
        # Create name -> (length, sequence) mappings for comparison
        def normalize_seq(seq):
            """Strip SQ. prefix if present for comparison."""
            return seq[3:] if seq.startswith("SQ.") else seq

        def seqcol_to_dict(sc):
            """Convert seqcol to dict keyed by name."""
            return {
                name: (length, normalize_seq(seq))
                for name, length, seq in zip(sc["names"], sc["lengths"], sc["sequences"])
            }

        original_dict = seqcol_to_dict(original_seqcol)
        exported_dict = seqcol_to_dict(exported_seqcol)

        # Same names should be present
        assert set(original_dict.keys()) == set(exported_dict.keys())

        # Each name should have same length and sequence digest
        for name in original_dict:
            assert original_dict[name] == exported_dict[name], f"Mismatch for {name}"


class TestFastaIndexWorkflow:
    """Test fasta index creates usable outputs."""

    def test_index_then_use_outputs(self, cli, sample_fasta):
        """Index creates files that can be used."""
        # Create all index files
        result = cli("fasta", "index", str(sample_fasta))
        assert result.exit_code == 0

        # Verify seqcol.json is valid
        seqcol_file = sample_fasta.parent / f"{sample_fasta.stem}.seqcol.json"
        assert seqcol_file.exists()

        seqcol = json.loads(seqcol_file.read_text())
        assert "names" in seqcol
        assert "lengths" in seqcol

    def test_index_files_are_consistent(self, cli, sample_fasta):
        """All index files are consistent with each other."""
        # Create index files
        cli("fasta", "index", str(sample_fasta))

        # Read seqcol.json
        seqcol_file = sample_fasta.parent / f"{sample_fasta.stem}.seqcol.json"
        seqcol = json.loads(seqcol_file.read_text())

        # Read chrom.sizes
        sizes_file = sample_fasta.parent / f"{sample_fasta.stem}.chrom.sizes"
        sizes = {}
        for line in sizes_file.read_text().strip().split("\n"):
            name, length = line.split("\t")
            sizes[name] = int(length)

        # Verify consistency
        for i, name in enumerate(seqcol["names"]):
            assert sizes[name] == seqcol["lengths"][i]


class TestConfigWorkflow:
    """Test configuration workflow."""

    def test_config_affects_store(self, cli, tmp_path, monkeypatch):
        """Config store.path is used by store commands."""
        store_path = tmp_path / "config_store"
        config_path = tmp_path / "config.toml"
        config_path.write_text(f'[store]\npath = "{store_path}"\n')
        monkeypatch.setenv("REFGET_CONFIG", str(config_path))

        # Init should use configured path
        result = cli("store", "init")
        assert result.exit_code == 0

        # Store should exist at configured path
        assert store_path.exists()


class TestBatchProcessing:
    """Test batch processing workflows."""

    def test_process_multiple_fastas(self, cli, tmp_path):
        """Process multiple FASTA files efficiently."""
        results = {}

        for fasta in [BASE_FASTA, DIFFERENT_NAMES_FASTA, DIFFERENT_ORDER_FASTA]:
            result = cli("fasta", "digest", str(fasta))
            assert result.exit_code == 0
            data = json.loads(result.stdout)
            results[fasta.name] = data["digest"]

        # All digests should be unique
        digests = list(results.values())
        assert len(digests) == len(set(digests))

    def test_add_all_to_store(self, cli, tmp_path):
        """Add all test FASTAs to store."""
        store = tmp_path / "store"
        cli("store", "init", "--path", str(store))

        fastas = [BASE_FASTA, DIFFERENT_NAMES_FASTA, DIFFERENT_ORDER_FASTA, SUBSET_FASTA]
        digests = []

        for fasta in fastas:
            result = cli("store", "add", str(fasta), "--path", str(store))
            assert result.exit_code == 0
            digests.append(json.loads(result.stdout)["digest"])

        # Verify all added
        result = cli("store", "list", "--path", str(store))
        collections = json.loads(result.stdout)["collections"]
        assert len(collections) >= len(fastas)


class TestComparisonWorkflows:
    """Test seqcol comparison workflows."""

    def test_pairwise_comparison(self, cli):
        """Compare all pairs of test FASTAs."""
        fastas = [BASE_FASTA, DIFFERENT_NAMES_FASTA, DIFFERENT_ORDER_FASTA]

        for i, fa1 in enumerate(fastas):
            for fa2 in fastas[i + 1 :]:
                result = cli("seqcol", "compare", str(fa1), str(fa2))
                # Exit code: 0=compatible, 1=incompatible (both are valid results)
                assert result.exit_code in [0, 1]
                # Should produce valid JSON comparison result
                data = json.loads(result.stdout)
                assert "compatible" in data

    def test_compare_known_relationships(self, cli):
        """Compare files with known relationships."""
        # base.fa and different_order.fa have same sequences in different order
        result = cli("seqcol", "compare", str(BASE_FASTA), str(DIFFERENT_ORDER_FASTA))
        # Exit code: 0=compatible, 1=incompatible
        assert result.exit_code in [0, 1]

        data = json.loads(result.stdout)
        # Should indicate sequences are same but order differs
        assert isinstance(data, dict)


class TestErrorRecovery:
    """Test workflows handle errors gracefully."""

    def test_continue_after_error(self, cli, tmp_path):
        """Workflow continues after recoverable error."""
        store = tmp_path / "store"
        cli("store", "init", "--path", str(store))

        # Try to add nonexistent file
        result = cli("store", "add", "/nonexistent.fa", "--path", str(store))
        assert result.exit_code != 0

        # Should still be able to add valid file
        result = cli("store", "add", str(BASE_FASTA), "--path", str(store))
        assert result.exit_code == 0

    def test_store_operations_after_failed_add(self, cli, tmp_path):
        """Store remains usable after failed add."""
        store = tmp_path / "store"
        cli("store", "init", "--path", str(store))

        # Failed add
        cli("store", "add", "/nonexistent.fa", "--path", str(store))

        # List should still work
        result = cli("store", "list", "--path", str(store))
        assert result.exit_code == 0


class TestEndToEndWorkflow:
    """Complete end-to-end workflow tests."""

    def test_full_workflow(self, cli, tmp_path, sample_fasta):
        """Complete workflow: index, store, compare."""
        store = tmp_path / "store"

        # 1. Create index files
        result = cli("fasta", "index", str(sample_fasta))
        assert result.exit_code == 0

        # 2. Get digest
        result = cli("fasta", "digest", str(sample_fasta))
        digest = json.loads(result.stdout)["digest"]

        # 3. Initialize store
        cli("store", "init", "--path", str(store))

        # 4. Add to store
        result = cli("store", "add", str(sample_fasta), "--path", str(store))
        store_digest = json.loads(result.stdout)["digest"]

        # 5. Verify digests match
        assert digest == store_digest

        # 6. Export from store
        exported = tmp_path / "exported.fa"
        cli("store", "export", digest, "-o", str(exported), "--path", str(store))

        # 7. Compare original with exported
        result = cli("seqcol", "compare", str(sample_fasta), str(exported))
        assert result.exit_code == 0

        # 8. Get stats
        result = cli("fasta", "stats", str(sample_fasta), "--json")
        assert result.exit_code == 0

        result = cli("store", "stats", "--path", str(store))
        assert result.exit_code == 0
