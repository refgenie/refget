"""The service subpackage must stay off the base-install import path.

``refget.seqcolapi`` imports fastapi, starlette and (via ``main``) sqlmodel at
module level, which is fine only for as long as nothing on the plain
``import refget`` path reaches it. These tests are the tripwire for that: they
run in a fresh interpreter, because ``sys.modules`` in the pytest process is
already polluted by the rest of the suite.
"""

import subprocess
import sys

import pytest

GATED_TOP_LEVEL = ("fastapi", "starlette", "uvicorn", "sqlmodel", "sqlalchemy", "psycopg2")


def _run(code: str) -> str:
    proc = subprocess.run(
        [sys.executable, "-c", code], capture_output=True, text=True, check=False
    )
    assert proc.returncode == 0, proc.stderr
    return proc.stdout.strip()


def test_import_refget_does_not_load_the_service_subpackage():
    loaded = _run(
        "import sys, refget;"
        "print(','.join(sorted(m for m in sys.modules if m.startswith('refget.seqcolapi'))))"
    )
    assert loaded == ""


def test_import_refget_does_not_load_heavy_dependencies():
    loaded = _run(
        "import sys, refget;"
        f"tops = {GATED_TOP_LEVEL!r};"
        "print(','.join(sorted({m.split('.')[0] for m in sys.modules} & set(tops))))"
    )
    assert loaded == ""


def test_import_refget_cli_does_not_load_heavy_dependencies():
    loaded = _run(
        "import sys, refget.cli;"
        f"tops = {GATED_TOP_LEVEL!r};"
        "print(','.join(sorted({m.split('.')[0] for m in sys.modules} & set(tops))))"
    )
    assert loaded == ""


def test_service_subpackage_is_importable_when_deps_are_present():
    # The suite installs the `test` extra, so fastapi is available here.
    loaded = _run(
        "import sys, refget.seqcolapi;"
        "print('fastapi' in sys.modules and hasattr(refget.seqcolapi, 'create_seqcol_app'))"
    )
    assert loaded == "True"


@pytest.mark.parametrize("blocked", ["fastapi", "sqlmodel"])
def test_missing_service_deps_raise_an_actionable_error(blocked):
    # Simulate a base install by making one gated dependency unimportable.
    message = _run(
        "import sys;"
        f"blocked = {blocked!r};"
        "sys.meta_path.insert(0, type('Blocker', (), {"
        "  'find_spec': staticmethod("
        "     lambda name, path=None, target=None: "
        "     (_ for _ in ()).throw(ImportError('blocked')) "
        "     if name.split('.')[0] == blocked else None)"
        "})());"
        "\ntry:\n"
        "    import refget.seqcolapi\n"
        "except ImportError as e:\n"
        "    print(str(e).replace(chr(10), ' '))\n"
    )
    assert "refget[seqcolapi]" in message
    assert "pip install" in message
    assert blocked in message
