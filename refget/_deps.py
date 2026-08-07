"""Optional-dependency gates.

refget ships several modules that require optional dependencies: the service
subpackage needs fastapi, the database modules need sqlmodel/sqlalchemy. Those
dependencies are imported at module level inside the modules that own them --
see the module-boundary rule in ``refget/models.py`` and
``refget/seqcolapi/__init__.py``. This module supplies the one thing that has
to run *before* those imports: a check that turns a missing extra into a
sentence telling you what to type, instead of a ``ModuleNotFoundError`` raised
from four imports deep in somebody else's package.

Keep this module import-light. It is loaded on paths that must not pull in the
very dependencies it is checking for, so it probes with
``importlib.util.find_spec`` rather than importing.
"""

from importlib.util import find_spec

__all__ = ["require"]


def _findable(name: str) -> bool:
    try:
        return find_spec(name) is not None
    except (ImportError, ValueError):
        # ImportError: a parent package is itself missing or broken.
        # ValueError: the module is present in sys.modules but has no spec.
        return False


def require(what: str, extra: str, *modules: str) -> None:
    """Raise an actionable ImportError if any of ``modules`` is unavailable.

    Probes rather than wrapping the caller's imports, so that a genuine
    ImportError raised from *inside* an installed dependency still surfaces as
    itself instead of being mistranslated into "not installed".

    Args:
        what: What the caller is, phrased for the error message, e.g.
            ``"refget.models defines the SQLModel database tables and"``.
        extra: The pip extra that supplies the dependencies, e.g. ``"db"``.
            Rendered as ``pip install 'refget[db]'``.
        *modules: Top-level module names to probe.
    """
    missing = [name for name in modules if not _findable(name)]
    if not missing:
        return
    raise ImportError(
        f"{what} requires the optional '{extra}' dependencies, and "
        f"{', '.join(missing)} {'is' if len(missing) == 1 else 'are'} not "
        f"installed.\nInstall them with:  pip install 'refget[{extra}]'"
    )
