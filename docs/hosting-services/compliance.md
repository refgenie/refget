# Compliance testing

Run compliance tests to verify your server correctly implements the GA4GH sequence collections API.

## Prerequisites

1. **Install pytest** (if not already installed):
   ```bash
   pip install pytest
   ```

2. **Clone the refget repository** (tests are in the repo, not the installed package):
   ```bash
   git clone https://github.com/refgenie/refget.git
   cd refget
   ```

3. **Load test data** into your server from the `test_fasta` folder

## Running the tests

Basic usage:

```bash
# Test the default public server
pytest tests/api

# Test a custom server
pytest tests/api --api-root http://127.0.0.1:8100

# Skip sorted_name_length_pairs tests
pytest tests/api --api-root https://your-server.com --no-snlp
```

## Complete example

Test your own server implementation:

```bash
# 1. Load test FASTA files into your database
refget admin load test_fasta/base.fa
refget admin load test_fasta/different_names.fa
# ... load other test files

# 2. Start your server
uvicorn myapp:app --port 8100

# 3. Run compliance tests
pytest tests/api --api-root http://127.0.0.1:8100
```

Test the public server:

```bash
pytest tests/api --api-root https://seqcolapi.databio.org --no-snlp
```

## Troubleshooting

### "Collection not found" errors

- Ensure you've loaded all test FASTA files from `test_fasta/` into your database
- Check that your server is running and accessible at the specified URL
- Verify your database connection settings

### Comparison tests failing

- The comparison endpoint must return the exact format specified in the GA4GH spec
- Check that `arrays`, `elements`, and `a_and_b_same_order` fields are present
- Ensure attribute digests match between collections

### sorted_name_length_pairs failures

- This is an optional but recommended attribute
- Use `--no-snlp` to skip these tests if your server doesn't implement it
- If implementing, ensure the digest is computed correctly (sorted array of name-length pair digests)

### Connection errors

- Verify the server URL is correct (include protocol: `http://` or `https://`)
- Check firewall settings if testing a remote server
- Ensure the server is running and responding to requests

## Test output

Successful tests show:

```
tests/api/test_compliance.py::test_collection_retrieval PASSED
tests/api/test_compliance.py::test_comparison PASSED
...
```

Failed tests include details about what went wrong:

```
FAILED tests/api/test_compliance.py::test_comparison - AssertionError: ...
```

Use `-v` for verbose output or `-vv` for extra details.

## What the tests verify

The compliance tests check:

- **Collection retrieval**: Can retrieve collections at level 1 and level 2
- **Attribute retrieval**: Can retrieve individual attributes by digest
- **Comparison endpoint**: Comparison function returns correct results
- **Sorted name-length pairs**: Optional attribute for coordinate system compatibility
