# seqcolapi

This repository contains:

1. Sequence collections API software (the `seqcolapi` package). This package is based on the `refget` package. It simply provides an wrapper to implement the Sequence Collections API.
2. Configuration and GitHub Actions for demo server instance ([deployment subfolder](/deployment)).

## Instructions

### Run locally for development

First, configure env vars:
- To run a local server with a **local database**:`source deployment/localhost/dev_local.env`
- To run a local server with **the production database**:`source deployment/seqcolapi.databio.org/production.env`

```
source deployment/sqlmodel/dev_sqlmodel.env

```


Then, run service:

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

## To load new data into seqcolapi.databio.org

See instructions in `seqcolapi` repo.
```
cd analysis
source ../servers/localhost/dev_local.env
ipython3
```

Now run `load_fasta.py`

## Deploy to AWS ECS

- Test locally first, using 1. native test; 2. local docker test.

### Deploying

To upgrade the software:

Use config file located in `/servers/seqcolapi.databio.org`. This will use the image in docker.io://databio/seqcolapi, github repo: [refgenie/seqcolapi](https://github.com/refgenie/seqcolapi) as base, bundle it with the above config, and deploy to the shefflab ECS.

1. Ensure the [refget](https://github.com/refgenie/refget/) package master branch is as you want it.
2. Deploy the updated [secqolapi](https://github.com/refgenie/seqcolapi/) app to dockerhub (using manual dispatch, or deploy on github release).
3. Finally, deploy the instance with manual dispatch using the included GitHub action.


