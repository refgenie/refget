# Changelog

All notable changes to the refget package will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- **`refget.seqcolapi` ships in the wheel.** The service code moved from the
  top-level `seqcolapi/` directory into `refget/seqcolapi/`, so a
  `pip install 'refget[seqcolapi]'` can serve the API with no repository
  checkout. Run it as `uvicorn refget.seqcolapi.main:store_app` (store-backed)
  or `uvicorn refget.seqcolapi.main:app` (PostgreSQL-backed).
- **`refget.seqcolapi.create_seqcol_app`**: a store-backed app factory that
  returns a self-contained, mountable FastAPI app, so a host application can
  mount the seqcol API under a prefix and keep its own `/service-info`.
- **`create_refget_router(mount_prefix=...)`**: lets the compliance endpoints
  self-target the seqcol service rather than the server root when the router is
  included under a prefix.
- **`db` extra**: `pip install 'refget[db]'` installs just the SQLModel layer
  (`refget.models`, `refget.agents`, `refget admin`) with no web server.
- Importing a module without its extra now raises an error naming the extra to
  install, rather than a bare `ModuleNotFoundError`.

### Changed

- **Distribution: `sqlmodel` is no longer a base dependency.** It moved out of
  the base install into the new `db` extra, and out of the `seqcolapi` extra,
  which now installs fastapi and uvicorn only. **If you import
  `refget.models`, `refget.agents`, or run `refget admin`, install
  `refget[db]`.** The PostgreSQL-backed service now needs
  `refget[seqcolapi-db]` (equivalent to `refget[seqcolapi,db]`); the
  store-backed service needs only `refget[seqcolapi]` and pulls no ORM.
- **`ubiquerg` removed from the `seqcolapi` extra.** Nothing under `refget/`
  imports it.
- `refget store serve` now builds its app with
  `refget.seqcolapi.create_seqcol_app` instead of hand-wiring FastAPI, so it
  serves the same routes the deployments do — notably `/service-info`, which it
  previously omitted — plus a permissive CORS middleware.
- `refget.seqcolapi.main.create_store_app` was renamed to
  `create_seqcolapi_store_app`, so that it is not confused with the generic
  `refget.seqcolapi.create_seqcol_app`: it carries the seqcolapi.databio.org
  service identity (`org.databio.seqcolapi.store`) and the SCOM service-info
  block. The `uvicorn refget.seqcolapi.main:store_app` entry point is unchanged.
- HTTP response models moved from `refget.models` (SQLModel) to
  `refget.response_models` (plain pydantic), so serving the API needs no ORM.

### Removed

- **`refget.router.compliance_router`** — the module-level router singleton is
  gone. It is replaced by `create_refget_router(compliance=True)` (the default),
  which builds the compliance routes per router so they can self-target a
  mounted prefix. No deprecation alias is provided on purpose: a module-level
  singleton can only be built with an empty `mount_prefix`, and would therefore
  silently reintroduce the root-targeting bug this replacement fixes. Nothing
  in-tree used the name.
- `python -m seqcolapi` / `python -m refget.seqcolapi` — both `__main__.py`
  modules imported a `main()` that has never existed, so both raised
  `ImportError` on every invocation. Use the `refget` CLI, or uvicorn with one
  of the app paths above.

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
