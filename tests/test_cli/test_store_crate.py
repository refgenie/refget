# tests/test_cli/test_store_crate.py

"""Tests for refget store crate CLI command."""

import importlib.util
import json
import os

_conftest_path = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "conftest.py"
)
_spec = importlib.util.spec_from_file_location("tests_conftest", _conftest_path)
_conftest = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_conftest)

BASE_FASTA = _conftest.BASE_FASTA
assert_json_output = _conftest.assert_json_output


def _init_and_add(cli, tmp_path):
    """Initialize a store and add a FASTA, return store_path."""
    store_path = tmp_path / "store"
    cli("store", "init", "--path", str(store_path))
    cli("store", "add", str(BASE_FASTA), "--path", str(store_path))
    return store_path


class TestStoreCrate:
    """Tests for: refget store crate"""

    def test_produces_valid_json(self, cli, tmp_path):
        """Crate command produces valid JSON output file."""
        store_path = _init_and_add(cli, tmp_path)

        result = cli(
            "store", "crate",
            "--path", str(store_path),
            "--name", "Test Store",
        )

        assert result.exit_code == 0
        crate_path = store_path / "ro-crate-metadata.json"
        assert crate_path.exists()

        crate = json.loads(crate_path.read_text())
        assert "@context" in crate
        assert "@graph" in crate
        assert isinstance(crate["@graph"], list)

    def test_has_must_entities(self, cli, tmp_path):
        """Crate contains all MUST entities per the profile."""
        store_path = _init_and_add(cli, tmp_path)

        cli(
            "store", "crate",
            "--path", str(store_path),
            "--name", "Test Store",
        )

        crate = json.loads((store_path / "ro-crate-metadata.json").read_text())
        ids = {e["@id"] for e in crate["@graph"]}

        # MUST entities
        assert "ro-crate-metadata.json" in ids
        assert "./" in ids
        assert "rgstore.json" in ids
        assert "sequences.rgsi" in ids
        assert "sequences/" in ids
        assert "collections/" in ids

    def test_metadata_descriptor_conformsto(self, cli, tmp_path):
        """Metadata descriptor has correct conformsTo."""
        store_path = _init_and_add(cli, tmp_path)

        cli(
            "store", "crate",
            "--path", str(store_path),
            "--name", "Test Store",
        )

        crate = json.loads((store_path / "ro-crate-metadata.json").read_text())
        descriptor = next(e for e in crate["@graph"] if e["@id"] == "ro-crate-metadata.json")

        conforms = [c["@id"] for c in descriptor["conformsTo"]]
        assert "https://w3id.org/ro/crate/1.2" in conforms
        assert "https://w3id.org/ga4gh/refget/refgetstore-crate/0.1" in conforms

    def test_root_dataset_name(self, cli, tmp_path):
        """Root dataset has the specified name."""
        store_path = _init_and_add(cli, tmp_path)

        cli(
            "store", "crate",
            "--path", str(store_path),
            "--name", "My Genome Store",
        )

        crate = json.loads((store_path / "ro-crate-metadata.json").read_text())
        root = next(e for e in crate["@graph"] if e["@id"] == "./")
        assert root["name"] == "My Genome Store"

    def test_property_values(self, cli, tmp_path):
        """Crate contains PropertyValue entities with correct stats."""
        store_path = _init_and_add(cli, tmp_path)

        cli(
            "store", "crate",
            "--path", str(store_path),
            "--name", "Test Store",
        )

        crate = json.loads((store_path / "ro-crate-metadata.json").read_text())
        props = {
            e["propertyID"]: e["value"]
            for e in crate["@graph"]
            if e.get("@type") == "PropertyValue"
        }

        assert "storageMode" in props
        assert "sequenceCount" in props
        assert props["sequenceCount"] > 0
        assert "collectionCount" in props
        assert props["collectionCount"] >= 1
        assert props["refgetDigestAlgorithm"] == "sha512t24u"

    def test_author_parsing_orcid(self, cli, tmp_path):
        """Parses 'Name <ORCID>' format into Person entity."""
        store_path = _init_and_add(cli, tmp_path)

        cli(
            "store", "crate",
            "--path", str(store_path),
            "--name", "Test Store",
            "--author", "Jane Doe <https://orcid.org/0000-0001-1234-5678>",
        )

        crate = json.loads((store_path / "ro-crate-metadata.json").read_text())

        # Find Person entity
        person = next(
            (e for e in crate["@graph"] if e.get("@type") == "Person"),
            None,
        )
        assert person is not None
        assert person["@id"] == "https://orcid.org/0000-0001-1234-5678"
        assert person["name"] == "Jane Doe"

        # Root dataset references author
        root = next(e for e in crate["@graph"] if e["@id"] == "./")
        assert root["author"]["@id"] == "https://orcid.org/0000-0001-1234-5678"

    def test_author_plain_name(self, cli, tmp_path):
        """Handles plain name without URL."""
        store_path = _init_and_add(cli, tmp_path)

        cli(
            "store", "crate",
            "--path", str(store_path),
            "--name", "Test Store",
            "--author", "John Smith",
        )

        crate = json.loads((store_path / "ro-crate-metadata.json").read_text())
        person = next(
            (e for e in crate["@graph"] if e.get("@type") == "Person"),
            None,
        )
        assert person is not None
        assert person["name"] == "John Smith"

    def test_license(self, cli, tmp_path):
        """License creates a CreativeWork entity."""
        store_path = _init_and_add(cli, tmp_path)

        cli(
            "store", "crate",
            "--path", str(store_path),
            "--name", "Test Store",
            "--license", "https://creativecommons.org/publicdomain/zero/1.0/",
        )

        crate = json.loads((store_path / "ro-crate-metadata.json").read_text())

        root = next(e for e in crate["@graph"] if e["@id"] == "./")
        assert root["license"]["@id"] == "https://creativecommons.org/publicdomain/zero/1.0/"

        license_entity = next(
            (e for e in crate["@graph"]
             if e["@id"] == "https://creativecommons.org/publicdomain/zero/1.0/"),
            None,
        )
        assert license_entity is not None
        assert license_entity["@type"] == "CreativeWork"

    def test_custom_output_path(self, cli, tmp_path):
        """Writes to custom output path."""
        store_path = _init_and_add(cli, tmp_path)
        output_path = tmp_path / "custom" / "crate.json"

        result = cli(
            "store", "crate",
            "--path", str(store_path),
            "--name", "Test Store",
            "--output", str(output_path),
        )

        assert result.exit_code == 0
        assert output_path.exists()

        crate = json.loads(output_path.read_text())
        assert "@graph" in crate

    def test_no_aliases_when_absent(self, cli, tmp_path):
        """Does not include aliases/ when directory doesn't exist."""
        store_path = _init_and_add(cli, tmp_path)

        # Remove aliases dir if it exists
        aliases = store_path / "aliases"
        if aliases.exists():
            import shutil
            shutil.rmtree(aliases)

        cli(
            "store", "crate",
            "--path", str(store_path),
            "--name", "Test Store",
        )

        crate = json.loads((store_path / "ro-crate-metadata.json").read_text())
        ids = {e["@id"] for e in crate["@graph"]}
        assert "aliases/" not in ids

    def test_create_action_provenance(self, cli, tmp_path):
        """Crate includes CreateAction with refget version."""
        store_path = _init_and_add(cli, tmp_path)

        cli(
            "store", "crate",
            "--path", str(store_path),
            "--name", "Test Store",
        )

        crate = json.loads((store_path / "ro-crate-metadata.json").read_text())

        action = next(
            (e for e in crate["@graph"] if e.get("@type") == "CreateAction"),
            None,
        )
        assert action is not None
        assert "endTime" in action
        assert action["instrument"]["@id"] == "#refget-software"

        sw = next(
            (e for e in crate["@graph"] if e["@id"] == "#refget-software"),
            None,
        )
        assert sw is not None
        assert sw["@type"] == "SoftwareApplication"
        assert "version" in sw

    def test_description_optional(self, cli, tmp_path):
        """Description is included when provided, absent when not."""
        store_path = _init_and_add(cli, tmp_path)

        # Without description
        cli(
            "store", "crate",
            "--path", str(store_path),
            "--name", "Test Store",
        )
        crate = json.loads((store_path / "ro-crate-metadata.json").read_text())
        root = next(e for e in crate["@graph"] if e["@id"] == "./")
        assert "description" not in root

        # With description
        cli(
            "store", "crate",
            "--path", str(store_path),
            "--name", "Test Store",
            "--description", "A test store for genomes",
        )
        crate = json.loads((store_path / "ro-crate-metadata.json").read_text())
        root = next(e for e in crate["@graph"] if e["@id"] == "./")
        assert root["description"] == "A test store for genomes"

    def test_empty_store(self, cli, tmp_path):
        """Crate works for empty store with zero counts."""
        store_path = tmp_path / "store"
        cli("store", "init", "--path", str(store_path))

        result = cli(
            "store", "crate",
            "--path", str(store_path),
            "--name", "Empty Store",
        )

        assert result.exit_code == 0
        crate = json.loads((store_path / "ro-crate-metadata.json").read_text())
        props = {
            e["propertyID"]: e["value"]
            for e in crate["@graph"]
            if e.get("@type") == "PropertyValue"
        }
        assert props["sequenceCount"] == 0
        assert props["collectionCount"] == 0
