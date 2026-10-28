# refget

The docs in `docs/` are published on https://docs.refgenie.org/refget/ by
databio/doc-hubs. `docs/docs.yml` holds the nav and the renderers.

## Notebooks vs Python Scripts for Tutorials

This project uses **percent-format `.py` files** instead of Jupyter notebooks (`.ipynb`) for executable tutorials.

### Comparison

|                          | `.ipynb`  | `.py`     |
|--------------------------|-----------|-----------|
| Inline output in editor  | Yes       | No        |
| Run as script            | Awkward   | Yes       |
| Clean git diffs          | No        | Yes       |
| AI editing               | Similar   | Similar   |

### Key Difference

In VS Code:
- **`.ipynb`**: Output renders inline, directly below the cell
- **`.py`**: Output renders in a separate Interactive Window panel

### Decision

We use `.py` files because:
1. **Runnable as scripts** - users can just `python tutorial.py`
2. **Clean version control** - plain text diffs, no JSON noise
3. **Still renders in the docs** - doc-hubs `hub-notebooks` renders percent-format `.py` files

### Percent Format

The `.py` files use percent format with `# %%` cell markers:

```python
# %% [markdown]
# # Tutorial Title
#
# Introduction text here.

# %%
import refget
store = refget.load("path/to/store")
print(store.stats())

# %% [markdown]
# ## Next Section
```

This format is recognized by:
- **doc-hubs** (`hub-notebooks`) - renders them as pages on docs.refgenie.org
- **VS Code** - shows "Run Cell" buttons (output goes to Interactive Window)
- **Jupyter** - can open directly with jupytext installed

### Capturing Output for Docs

There is no capture script (an earlier `examples/capture_outputs.py` no longer
exists in the `refget` repository). Since `.py` files don't store output,
output blocks are captured by hand: run the tutorial script and paste its
real stdout into the `# %% [markdown] output` comment block that follows the
cell, replacing whatever was there before.

```bash
# from an environment where the intended refget and gtars versions are installed
export PYTHONDONTWRITEBYTECODE=1
python -u docs/using-services/refgetstore.py
```

Run with `-u` (unbuffered) so progress lines interleave with `print()` output
in the same order a reader would see them if they ran the script themselves.
Make sure the `refget` CLI resolved by `PATH` (needed for cells that shell
out to it) comes from the same environment as the `python` running the
script -- a stray system install on `PATH` will silently capture stale output.

Paste the captured stdout into the matching output block:

```python
# %%
print("Hello")

# %% [markdown] output
# ```
# Hello
# ```
```

The output appears in the rendered docs but the file remains a valid,
directly runnable script. Only update the blocks whose content actually
changed -- don't recapture unrelated, still-correct cells just because the
script was re-run. Two caveats worth knowing when comparing a fresh capture
to what's documented: dict-valued output (like `store.stats()`) prints keys
in hash-map order, which varies between runs even though the values don't;
and any cell that opens a remote store depends on that remote being
reachable and unchanged.

### Location

The tutorials are the docs pages themselves: `docs/using-services/*.py`
(`refgetstore.py`, `aliases.py`, `genome-store.py`, `fhr-metadata.py`,
`seqcol-operations.py`). There is no separate source copy elsewhere in the
`refget` repository -- edit the file under `docs/using-services/`
directly, run it as shown above, and update its output blocks in place.

### Adding a tutorial

Add the file to `hub-notebooks.include` and to `nav` in `docs/docs.yml`.
