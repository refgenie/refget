"""Tripwires for the optional-dependency boundaries.

refget has three install tiers, and each one is a promise about what does *not*
get imported:

* base (``pip install refget``) -- no fastapi, no sqlmodel, no sqlalchemy.
* ``refget[seqcolapi]`` -- fastapi, but still **no database**. The
  RefgetStore-backed service must run with no ORM in the environment.
* ``refget[seqcolapi-db]`` -- everything, for the PostgreSQL app.

Those promises are enforced by module boundaries, which are easy to break by
adding one innocent-looking top-level import. These tests run in a fresh
interpreter, because ``sys.modules`` in the pytest process is already polluted
by the rest of the suite.
"""

import os
import subprocess
import sys

import pytest

DB_TOP_LEVEL = ("sqlmodel", "sqlalchemy", "psycopg2")
GATED_TOP_LEVEL = ("fastapi", "starlette", "uvicorn") + DB_TOP_LEVEL

# Blocks top-level distributions from being imported *or* found by find_spec,
# which is how refget._deps.require probes. Simulates a narrower install.
_BLOCKER = (
    "import sys;"
    "blocked = {blocked!r};"
    "sys.meta_path.insert(0, type('Blocker', (), {{"
    "  'find_spec': staticmethod("
    "     lambda name, path=None, target=None: "
    "     (_ for _ in ()).throw(ImportError('blocked')) "
    "     if name.split('.')[0] in blocked else None)"
    "}})());"
)


def _run(code: str, env: dict = None) -> str:
    proc = subprocess.run(
        [sys.executable, "-c", code], capture_output=True, text=True, check=False, env=env
    )
    assert proc.returncode == 0, proc.stderr
    return proc.stdout.strip()


def _blocker(*blocked: str) -> str:
    return _BLOCKER.format(blocked=blocked)


def _report_loaded(*tops: str) -> str:
    """Print the gated top-level packages that ended up in sys.modules."""
    return (
        f"tops = {tops!r};"
        "print('LOADED:' + ','.join(sorted({m.split('.')[0] for m in sys.modules} & set(tops))))"
    )


def _loaded_line(output: str) -> str:
    for line in output.splitlines():
        if line.startswith("LOADED:"):
            return line[len("LOADED:") :]
    raise AssertionError(f"no LOADED: line in output: {output!r}")


# --------------------------------------------------------------------------
# Base install: nothing heavy.
# --------------------------------------------------------------------------


def test_import_refget_does_not_load_the_service_subpackage():
    loaded = _run(
        "import sys, refget;"
        "print(','.join(sorted(m for m in sys.modules if m.startswith('refget.seqcolapi'))))"
    )
    assert loaded == ""


def test_import_refget_does_not_load_heavy_dependencies():
    out = _run("import sys, refget;" + _report_loaded(*GATED_TOP_LEVEL))
    assert _loaded_line(out) == ""


def test_import_refget_cli_does_not_load_heavy_dependencies():
    out = _run("import sys, refget.cli;" + _report_loaded(*GATED_TOP_LEVEL))
    assert _loaded_line(out) == ""


# --------------------------------------------------------------------------
# refget[seqcolapi]: fastapi, but no database. This is the boundary the `db`
# extra exists to make real -- a store-backed deployment must not need an ORM.
# --------------------------------------------------------------------------


def test_service_subpackage_is_importable_when_deps_are_present():
    # The suite installs the `test` extra, so fastapi is available here.
    loaded = _run(
        "import sys, refget.seqcolapi;"
        "print('fastapi' in sys.modules and hasattr(refget.seqcolapi, 'create_seqcol_app'))"
    )
    assert loaded == "True"


def test_router_does_not_load_the_database_layer():
    """refget.router's response models come from refget.response_models.

    If someone moves them back into refget.models, this fails -- and every
    store-backed deployment silently starts requiring sqlalchemy again.
    """
    out = _run("import sys, refget.router;" + _report_loaded(*DB_TOP_LEVEL))
    assert _loaded_line(out) == ""


def test_service_subpackage_does_not_load_the_database_layer():
    out = _run("import sys, refget.seqcolapi;" + _report_loaded(*DB_TOP_LEVEL))
    assert _loaded_line(out) == ""


def test_store_backed_app_builds_without_the_database_layer(tmp_path):
    """The headline capability: build the store app with sqlmodel unimportable."""
    out = _run(
        _blocker(*DB_TOP_LEVEL) + "import refget.seqcolapi as s;"
        f"app = s.create_seqcol_app(store_path={str(tmp_path)!r});"
        "print(type(app).__name__);" + _report_loaded(*DB_TOP_LEVEL)
    )
    assert out.splitlines()[0] == "FastAPI"
    assert _loaded_line(out) == ""


def test_main_module_store_app_does_not_load_the_database_layer(tmp_path):
    """``uvicorn seqcolapi.main:store_app`` must not drag in the ORM.

    ``app`` lives in refget.seqcolapi.dbapp and is resolved through main's
    module-level ``__getattr__``, so importing main and reading ``store_app``
    off it stays database-free.
    """
    env = dict(os.environ, REFGET_STORE_PATH=str(tmp_path))
    out = _run(
        "import sys, refget.seqcolapi.main as m;"
        "print(type(m.store_app).__name__);" + _report_loaded(*DB_TOP_LEVEL),
        env=env,
    )
    assert out.splitlines()[0] == "FastAPI"
    assert _loaded_line(out) == ""


def test_missing_fastapi_points_at_the_seqcolapi_extra():
    message = _run(
        _blocker("fastapi") + "\ntry:\n"
        "    import refget.seqcolapi\n"
        "except ImportError as e:\n"
        "    print(str(e).replace(chr(10), ' '))\n"
    )
    assert "refget[seqcolapi]" in message
    assert "pip install" in message
    assert "fastapi" in message


# --------------------------------------------------------------------------
# refget[db]: the ORM modules name their own extra.
# --------------------------------------------------------------------------


@pytest.mark.parametrize("module", ["refget.models", "refget.agents", "refget.seqcolapi.dbapp"])
def test_missing_sqlmodel_points_at_the_db_extra(module):
    message = _run(
        _blocker(*DB_TOP_LEVEL) + "\ntry:\n"
        f"    import {module}\n"
        "except ImportError as e:\n"
        "    print(str(e).replace(chr(10), ' '))\n"
    )
    assert "refget[db]" in message, message
    assert "pip install" in message, message
    assert "sqlmodel" in message, message
    # Names itself, rather than being a bare ModuleNotFoundError from four
    # imports deep in somebody else's package.
    assert module in message, message


def test_models_still_reexports_the_response_models():
    """Moving them to refget.response_models must not break existing imports."""
    loaded = _run(
        "from refget.models import PaginatedDigestList, PaginationResult, "
        "ResultsSequenceCollections, Similarities;"
        "print('ok')"
    )
    assert loaded == "ok"
