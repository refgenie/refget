# Refget

![Run pytests](https://github.com/pepkit/looper/workflows/Run%20pytests/badge.svg)

User-facing documentation is hosted at [refgenie.org/refget](https://refgenie.org/refget/).

This repository includes:

1. `/refget`: The `refget` Python package, which provides a Python interface to both remote and local use of refget standards. It has clients and functions for both refget sequences and refget sequence collections (seqcol).
2. `/seqcolapi`: Sequence collections API software, a FastAPI wrapper built on top of the `refget` package. It provides a bare-bones Sequence Collections API service.
3. `/deployment`: Server configurations for demo instances and public deployed instances. There are also github workflows (in `.github/workflows`) that deploy the demo server instance from this repository.
4. `/test_fasta` and `/test_api`: Dummy data and a compliance test, to test external implementations of the Refget Sequence Collections API.
5. `/frontend`: a React seqcolapi front-end.

## Testing

### Local unit tests of refget package

- `pytest` to test `refget` package, local unit tests

## Development and deployment: Backend

### Easy-peasy way

In a moment I'll show you how to do these steps individually, but if you're in a hurry, the easy way get a development API running for testing is to just use my very simple shell script like this (no data persistence, just loads demo data):

```console
bash deployment/demo_up.sh
```

This will:
- populate env vars
- launch postgres container with docker
- run the refget service with uvicorn
- load up the demo data
- block the terminal until you press Ctrl+C, which will shut down all services.

### Setting up a database connection

First configure a database connection through environment variables. Choose one of these:

```
source deployment/local_demo/local_demo.env # local demo (see below to create the database using docker)
source deployment/seqcolapi.databio.org/production.env # connect to production database
```

If you're using the `local_demo`, then use docker to launch a local postgres database service like this:

```
docker run --rm --name refget-postgres -p 127.0.0.1:5432:5432 \
  -e POSTGRES_PASSWORD \
  -e POSTGRES_USER \
  -e POSTGRES_DB \
  -e POSTGRES_HOST \
  postgres:17.0
```

If you need to load test data into your server, then you have to install [gtars](https://docs.bedbase.org/gtars/) (with `pip install gtars`), a Python package for computing GA4GH digests. You can then load test data like this:

```
python data_loaders/load_demo_data.py
```

or:

```
refget add-fasta -p test_fasta/test_fasta_metadata.csv -r test_fasta
```


### Running the seqcolapi API backend

Run the demo `seqcolapi` service like this:

```
uvicorn seqcolapi.main:app --reload --port 8100
```

### Running with docker

To build the docker file, first build the image from the root of this repository:

```
docker build -f deployment/dockerhub/Dockerfile -t databio/seqcolapi seqcolapi
```

To run in container:

```
source deployment/seqcolapi.databio.org/production.env
docker run --rm -p 8000:80 --name seqcolapi \
  --env "POSTGRES_USER" \
  --env "POSTGRES_DB" \
  --env "POSTGRES_PASSWORD" \
  --env "POSTGRES_HOST" \
  databio/seqcolapi
```

### Deploying container to dockerhub

Use the github action in this repo which deploys on release, or through manual dispatch.

## Running the frontend

Once you have a backend running, you can run a frontend to interact with it

### Local client with local server

```
cd frontend
npm i
VITE_API_BASE="http://localhost:8100" npm run dev
```

### Local client with production server

```
cd frontend
npm i
VITE_API_BASE="https://seqcolapi.databio.org" npm run dev
```

## Deploy to AWS ECS

- Test locally first, using 1. native test; 2. local docker test.

### Deploying

1. Ensure the [refget](https://github.com/refgenie/refget/) package master branch is as you want it.
2. Deploy the updated [secqolapi](https://github.com/refgenie/seqcolapi/) app to dockerhub (using manual dispatch, or deploy on github release).
3. Finally, deploy the instance with manual dispatch using the included GitHub action.

## Developer notes

### Models

The objects and attributes are represented as SQLModel objects in `refget/models.py`. To add a new attribute:

1. create a new model. This will create a table for that model, etc.
2. change the function that creates the objects, to populate the new attribute.




## Example of loading reference fasta datasets:

```
refget add-fasta -p ref_fasta.csv -r $BRICKYARD/datasets_downloaded/pangenome_fasta/reference_fasta
```
