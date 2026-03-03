# Changelog

All notable changes to the refget package will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.11.0] - 2026-02-28

This is a major release with significant restructuring, new features, and improved tooling.

### Added

- **CLI overhaul**: New `refget` CLI built with Typer, including subcommands for `store`, `seqcol`, `fasta`, `config`, and `admin`
- **Local store**: `refget store pull` command to pull sequence collections from remote servers to a local store
- **FASTA digesting**: `refget fasta digest` CLI command for computing sequence collection digests from FASTA files
- **Sequence collection similarities**: `calc_similarities` and `calc_similarities_from_json` functions with Jaccard similarity metrics and API endpoint
- **FASTA DRS objects**: `FastaDrsObject` model for serving FASTA files via DRS endpoints
- **Comparison interpreter**: Local sequence collection comparison interpretation module (SCIM)
- **Species filtering**: Filter similarities endpoint by species
- **Human-readable names**: `human_readable_name` field on `SequenceCollection` model
- **Pydantic API models**: Structured response models for API endpoints (fixes #33)
- **Swagger documentation**: API query parameter documentation
- **Frontend features**: Strip plots, one-to-many comparison view, FASTA digest tool, species selector, SCIM integration, dynamic version display
- **Compliance testing**: Comprehensive API compliance test suite
- **Integration test framework**: New integration test infrastructure with ephemeral databases
- **CLI test suite**: Extensive CLI tests covering store, seqcol, fasta, config, admin, and help commands
- **Service info**: `/service-info` endpoints for fasta_drs and refget_store features
- **Attribute listing**: `/list/attributes` endpoint per GA4GH paging guide
- **Bulk query**: Preload and bulk query support for sequence collections
- **R package**: First pass at `refget-r` R bindings (experimental)

### Changed

- **Switched to gtars**: Replaced pyfaidx and henge with gtars for FASTA parsing and digest computation
- **Major code restructure**: Consolidated schemas, reorganized modules, reduced code duplication
- **Improved error messages**: Better dependency error messages (fixes #49), clearer import errors
- **Performance optimizations**: Faster level 2 retrieval using `get_many`, optimized similarity calculations
- **Updated GA4GH compliance**: Aligned with latest refget sequence collections specification
- **Schema consolidation**: Single unified schema replacing multiple schema files
- **Collated attribute validation**: Validation for collated attributes in sequence collections
- **Frontend overhaul**: Updated comparison view, heatmap aliases, loading states, error handling

### Removed

- **Henge dependency**: Removed henge and biopython requirements
- **Legacy code**: Removed old flags code, duplicate functions, unused yacman imports

### Fixed

- `from_PySequenceCollection` construction and associated tests
- Circular dependency import issues in utilities
- Level 1 model representation
- Comparison links
- Cancel handling in frontend
- Various linting and type hint improvements

### Security

- Bumped frontend dependencies: vite, minimatch, rollup, esbuild, js-yaml, vega

## [0.10.1] - 2025-06-01

Previous release. See git history for details.
