# Changelog

This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html) and [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) format.


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

## [0.11.0] - 2026-03-18

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
- New gtars features exposed in the refget Python API: `compute_fai`, `digest_sequence`, and `SequenceCollection` available via `import refget`
- FHR metadata support: `refget store metadata` and `refget store metadata-set` commands for managing collection metadata
- Seqcol CLI commands (`show`, `compare`, `validate`) look up collections in the local store before querying remote servers
- Web UI compliance runner with real-time streaming results, a stop button, and per-test descriptions
- gtars version displayed in service-info and frontend footer badges
- Download collections in seqcol JSON format from the web UI

### Changed

- **Switched to gtars**: Replaced pyfaidx and henge with gtars for FASTA parsing and digest computation
- **Major code restructure**: Consolidated schemas, reorganized modules, reduced code duplication
- **Improved error messages**: Better dependency error messages (fixes #49), clearer import errors
- **Performance optimizations**: Faster level 2 retrieval using `get_many`, optimized similarity calculations
- **Updated GA4GH compliance**: Aligned with latest refget sequence collections specification
- **Schema consolidation**: Single unified schema replacing multiple schema files
- **Collated attribute validation**: Validation for collated attributes in sequence collections
- **Frontend overhaul**: Updated comparison view, heatmap aliases, loading states, error handling
- seqcolapi no longer has independent versioning; it now versions with refget

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

## [0.10.1] - 2026-01-27

- Fix CLI `store list` JSON serialization error (was returning non-serializable metadata objects)
- Fix CLI `store get`, `store remove`, and `store pull` commands that failed to find collections
- Update CLI to use `iter_collections()` API instead of removed `collections()` method

## [0.10.0] - 2026-01-26

- Major restructure of the package with new comprehensive CLI (`refget` command)
- New CLI subcommands: `admin`, `config`, `fasta`, `seqcol`, and `store`
- Implement FASTA DRS objects for serving FASTA files via GA4GH DRS endpoints
- Add RefgetStore integration for local sequence storage via gtars
- Refactor to isolate gtars dependency, improving import performance
- Add service-info capabilities for fasta_drs and refget_store features
- New integration test framework with ephemeral Docker PostgreSQL
- Comprehensive CLI test suite
- API compliance tests against GA4GH seqcol specification
- Fix endpoint path: `/list/collection` (was `/list/collections` in client)
- New browser-based `/digest` feature for computing seqcol digests from FASTA files entirely client-side using [@databio/gtars](https://www.npmjs.com/package/@databio/gtars) WASM module

## [0.9.0] - 2025-08-13

- performance fix for calculating jaccard similarties
- add human_readable_name list as an attribute to SequenceCollection for displaying similarity results
- adding SequenceCollections via PEP will now add associated sample_name as a human_readable_name
- add wrapper for gtars RefgetStore so it can be called directly from refget

## [0.8.3] - 2025-07-31

- adds API endpoints for jaccard similarity calculations
- some refactoring for newest gtars, v0.3.0
- add class method from_PySequenceCollection for creating SequenceCollection from a gtars-created SequenceCollection
- adds Similarity UI to frontend

## [0.8.2] - 2025-03-26

- updated add method to use boolean for updating SequenceCollection if already exists

## [0.8.1] - 2025-03-21

- addition of SCIM

## [0.8.0] - 2025-03-05

- Complete rewrite of the clients and agents.
- New SequenceAgent class allows using the RefgetDBAgent class to store sequences. This is meant for testing purposes.
- Completely refactored Clients work adds mature SequenceClient and SequenceCollectionClient classes.
- Fix issues with rust digest calculations to improve flexibilty, using latest update to gtars interface.
- Updates to latest ga4gh paging guidance
- Add a beta CLI with `digest-fasta` and `add-fasta` functionality.
- Remove some old stuff based on henge backend

## [0.7.0] - 2025-01-11

- Major revamp to RefGetClient object, which now works with either sequences or seqcol servers, and can handle any of the seqcol API endpoints.
- Better integration of rust digest calculations built on gtars
- switch back-end to use JSON instead of str
- implement name_length_pairs and sorted_sequences attrs
- improve some SeqCol object representations

## [0.6.0] - 2024-08-08

- Change paging style of list endpoints to match latest GA4GH pagination guide
- Implement new `/list/attribute` endpoint on back-end, and add to demo
- Update endpoint paths slightly after discussion for the `/list` and `/attribute` endpoints
- Remove some of the duplicate endpoints to solidify to one API

## [0.5.0] - 2024-07-06

- Work on deployment, container building, configuration
- Add some work toward pangenomes
- Various misc improvements

## [0.4.0] - 2024-06-26

- Implement new sqlmodel and agent for new database backend
- Add new React interface


## [0.3.0] - 2024-02-23

- Add seqcolapi router

## [0.2.0] - 2024-02-03

- Integrate seqcol into refget package.

## [0.1.0] - 2021-06-17

- First public version, backed by henge version 0.1.1.

## [0.0.1] - 2020-06-25

Beta version for testing
