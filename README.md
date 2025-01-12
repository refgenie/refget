# Refget

![Run pytests](https://github.com/pepkit/looper/workflows/Run%20pytests/badge.svg)

User-facing documentation is hosted at [refgenie.org/refget](https://refgenie.org/refget/).

In this repository you will find:

1. `/refget`: The `refget` Python package, which provides a Python interface to both remote and local use of the refget protocol. It has clients and functions for both refget sequences and refget sequence collections (seqcol).
2. `/seqcolapi`: Sequence collections API software, a FastAPI wrapper built on top of the `refget` package. It provides a bare-bones Sequence Collections API service.
3. `actions` (in `.github/workflows`):  GitHub Actions for demo server instance 
4. `/deployment`: Server configurations for demo instances and public deployed instances.
5. `/test_fasta` and `/test_api`: Dummy data and a compliance test, to test external implementations of the Refget Sequence Collections API.
6. `/frontend`: a React seqcolapi front-end.

## Testing

### Local unit tests of refget package

- `pytest` to test `refget` package, local unit tests

### Compliance testing of Sequence Collections API

Under `/test_api` are compliance tests for a service implementing the sequence collections API. This will test your collection and comparison endpoints to make sure the comparison function is working. 

- `pytest test_api` to tests API compliance
- `pytest test_api --api_root http://127.0.0.1:8100` to customize the API root URL to test

1. Load the fasta files from the `test_fasta` folder into your API database.
2. Run `pytest test_api --api_root <API_URL>`, pointing to your URL to test

For example, this will test a remote server instance:

```
pytest test_api --api_root https://seqcolapi.databio.org
```

## Development and deployment

### Setting up a database connection

First populate environment variables to configure a database connection. Choose one of these:

```
source deployment/local_demo/local_demo.env # local demo (see below to create the database using docker)
source deployment/seqcolapi.databio.org/production.env # connect to production database
```

If you're using the `local_demo`, then use docker to create a local postgres database like this:

```
docker run --rm --name refget-postgres -p 127.0.0.1:5432:5432 \
  -e POSTGRES_PASSWORD \
  -e POSTGRES_USER \
  -e POSTGRES_DB \
  -e POSTGRES_HOST \
  postgres:17.0
```

If you need to load test data into your server, then you have to install `gtars`, a Python package for computing GA4GH digests. You can load test data like this:

```
python load_demo_data.py
# refget add-fasta path/to/fasta.fa  # This could be a way in the future...
# python load_pangenome_reference.py ../seqcolapi/analysis/data/demo.csv test_fasta  # loads an entire pangenome
```

## Running the seqcolapi API backend

Run the demo `seqcolapi` service like this:

```
uvicorn seqcolapi.main:app --reload --port 8100
```

### Running with docker

To build the docker file, from the root of this repository:


First you build the general-purpose image

```
docker build -f deployment/dockerhub/Dockerfile -t databio/seqcolapi seqcolapi
```

Next you build the wrapped image (this just wraps the config into the app):

```
docker build -f deployment/seqcolapi.databio.org/Dockerfile -t seqcolapi.databio.org deployment/seqcolapi.databio.org
```

To run in a container:
```
source deployment/seqcolapi.databio.org/production.env
docker run --rm -p 8000:80 --name seqcolapi \
  --env "POSTGRES_USER" \
  --env "POSTGRES_DB" \
  --env "POSTGRES_PASSWORD" \
  --env "POSTGRES_HOST" \
  seqcolapi.databio.org
```

### Alternative: Mount the config

Instead of building a bundle with the config, you could just mount it into the base image:
```
docker run --rm -p 8000:8000 --name sccon \
  --env "POSTGRES_PASSWORD" \
  --volume $CODE/seqcolapi.databio.org/config/seqcolapi.yaml:/config.yaml \
  seqcolapi 
```

### Deploying container to dockerhub

Use github action in this repo which deploys on release, or through manual dispatch.


## Running the frontend

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

To upgrade the software:

Use config file located in `/servers/seqcolapi.databio.org`. This will use the image in docker.io://databio/seqcolapi, github repo: [refgenie/seqcolapi](https://github.com/refgenie/seqcolapi) as base, bundle it with the above config, and deploy to the shefflab ECS.

1. Ensure the [refget](https://github.com/refgenie/refget/) package master branch is as you want it.
2. Deploy the updated [secqolapi](https://github.com/refgenie/seqcolapi/) app to dockerhub (using manual dispatch, or deploy on github release).
3. Finally, deploy the instance with manual dispatch using the included GitHub action.








## Developer notes

### Models

The objects and attributes are represented as SQLModel objects in `refget/models.py`. To add a new attribute:

1. create a new model. This will create a table for that model, etc.
2. change the function that creates the objects, to populate the new attribute.


