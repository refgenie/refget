# Refget

![Run pytests](https://github.com/pepkit/looper/workflows/Run%20pytests/badge.svg)

The refget package provides a Python interface to both remote and local use of the refget protocol.

This package provides clients and functions for both refget sequences and refget sequence collections (seqcol).

Documentation is hosted at [refgenie.org/refget](https://refgenie.org/refget/).

## Testing

### Local unit tests of refget package

- `pytest` to test `refget` package, local unit tests

### Compliance testing 

Under `/test_api` are compliance tests for a service implementing the sequence collections API. This will test your collection and comparison endpoints to make sure the comparison function is working. 

- `pytest test_api` to tests API compliance
- `pytest test_api --api_root http://127.0.0.1:8100` to customize the API root URL to test

1. Load the fasta files from the `test_fasta` folder into your API database.
2. Run `pytest test_api --api_root <API_URL>`, pointing to your URL to test

For example, this will test my remote server instance:

```
pytest test_api --api_root https://seqcolapi.databio.org
```


## Loading up data into an instance

### Starting a demo instance 

Use docker to create a local postgres database like this:

```
docker run --rm --name refget-postgres -p 5432:5432 \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_DB=postgres \
  postgres:13
```

### Loading files

If you need to load, then you have to install either `gc_count` (fast) or `pyfaidx` (slow).

You can load them like:

```
python load_demo_data.py
```

Or:

```
refget add-fasta path/to/fasta.fa
```





