#!/usr/bin/env python3
"""
Run a percent-format .py file and insert captured outputs as markdown blocks.

Usage: python capture_outputs.py input.py > output.py

This captures ALL output including from Rust/C libraries by redirecting
at the file descriptor level, not just Python's sys.stdout.
"""

import os
import sys
import tempfile
from contextlib import contextmanager

@contextmanager
def capture_all_output():
    """Capture stdout/stderr at fd level (catches Rust/C output too)."""
    with tempfile.NamedTemporaryFile(mode='w+', delete=False) as tmp:
        tmp_path = tmp.name

    # Save state
    saved = (os.dup(1), os.dup(2), sys.stdout, sys.stderr)
    sys.stdout.flush()
    sys.stderr.flush()

    # Redirect
    tmp_file = open(tmp_path, 'w')
    os.dup2(tmp_file.fileno(), 1)
    os.dup2(tmp_file.fileno(), 2)
    sys.stdout = sys.stderr = tmp_file

    try:
        yield
    finally:
        # Restore
        sys.stdout.flush()
        tmp_file.close()
        os.dup2(saved[0], 1)
        os.dup2(saved[1], 2)
        os.close(saved[0])
        os.close(saved[1])
        sys.stdout, sys.stderr = saved[2], saved[3]

    # Return captured output
    with open(tmp_path) as f:
        capture_all_output.result = f.read()
    os.unlink(tmp_path)

def parse_cells(content):
    """Split percent-format file into cells."""
    cells = []
    current = {"type": "code", "lines": []}

    for line in content.splitlines(keepends=True):
        if line.strip().startswith("# %%"):
            if current["lines"]:
                cells.append(current)
            current = {
                "type": "markdown" if "[markdown]" in line else "code",
                "lines": [line]
            }
        else:
            current["lines"].append(line)

    if current["lines"]:
        cells.append(current)
    return cells

def main():
    if len(sys.argv) < 2:
        print("Usage: python capture_outputs.py input.py", file=sys.stderr)
        sys.exit(1)

    content = open(sys.argv[1]).read()
    cells = parse_cells(content)
    env = {"__name__": "__main__"}

    for cell in cells:
        # Print the cell content
        print("".join(cell["lines"]), end="")

        # Execute code cells and capture output
        if cell["type"] == "code":
            code = "".join(cell["lines"][1:])  # Skip the # %% line
            if code.strip():
                with capture_all_output():
                    try:
                        exec(code, env)
                    except Exception as e:
                        print(f"Error: {e}")

                output = capture_all_output.result
                if output.strip():
                    print(f"\n# %% [markdown]")
                    print(f"# ```")
                    for line in output.rstrip().splitlines():
                        print(f"# {line}")
                    print(f"# ```\n")

if __name__ == "__main__":
    main()
