"""
BLAST commands for the refget CLI.

``refget blast VERB ...`` runs ``gtars blast VERB ...`` in this process (``gtars.blast._main``):
the same verbs, flags, help, output and exit codes. ``refget blast --help`` lists the verbs.
For verbs that read a store, ``-p/--path`` or ``-r/--remote`` (default: the configured store)
become ``--store``; ``search`` and ``origin`` with ``--db`` (``--engine blastn``) search that
database and get no store.
"""

from pathlib import Path
from typing import List, Optional

import typer

from refget.cli.output import EXIT_FAILURE, print_error
from refget.cli.store import _get_store_path

# The verbs that take --store.
STORE_VERBS = {"build", "verify", "nstats", "search", "origin", "reps"}
HELP = "BLAST over a RefgetStore: build databases, search, and report where hits come from"


def store_argv(args: List[str]) -> List[str]:
    """Map ``-p/--path`` and ``-r/--remote`` to ``--store`` for verbs that take a store.

    Without either (and without ``--store``), the configured store is used, except for
    ``search`` and ``origin`` with ``--db``. Arguments after ``--`` belong to the search engine
    and are left alone.
    """
    if not args or args[0] not in STORE_VERBS:
        return args
    verb, rest = args[0], args[1:]
    path: Optional[str] = None
    remote: Optional[str] = None
    out: List[str] = []
    i = 0
    while i < len(rest):
        a = rest[i]
        if a == "--":
            out += rest[i:]
            break
        name, eq, val = a.partition("=")
        if name in ("-p", "--path", "-r", "--remote"):
            if not eq:
                if i + 1 >= len(rest):
                    out.append(a)
                    break
                val = rest[i + 1]
                i += 1
            if name in ("-p", "--path"):
                path = val
            else:
                remote = val
            i += 1
            continue
        out.append(a)
        i += 1
    if any(a == "--store" or a.startswith("--store=") for a in out):
        return [verb, *out]
    if any(a in ("-h", "--help") for a in out):
        return [verb, *out]
    own = out[: out.index("--")] if "--" in out else out
    has_db = any(a == "--db" or a.startswith("--db=") for a in own)
    if verb in ("search", "origin") and has_db and not (path or remote):
        return [verb, *out]
    store = remote or str(_get_store_path(Path(path) if path else None))
    return [verb, "--store", store, *out]


def blast(ctx: typer.Context) -> None:
    """BLAST over a RefgetStore (gtars blast; refget blast --help lists the verbs)."""
    try:
        from gtars.blast import _main
    except ImportError:
        print_error(
            "this gtars build has no BLAST support; install a gtars release that ships gtars.blast",
            EXIT_FAILURE,
        )
    raise typer.Exit(_main("refget blast", store_argv(list(ctx.args))))
