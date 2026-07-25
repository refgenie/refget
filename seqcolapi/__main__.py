"""Compatibility shim: ``python -m seqcolapi`` -> ``python -m refget.seqcolapi``."""

import runpy

runpy.run_module("refget.seqcolapi", run_name="__main__", alter_sys=True)
