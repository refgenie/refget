# seqcolapi

This repository contains:

1. Sequence collections API software (the `seqcolapi` package). This package is based on the `refget` package. It simply provides an wrapper to implement the Sequence Collections API.
2. Configuration and GitHub Actions for demo server instance ([servers subfolder](/servers)).

## Instructions

### Run locally for development

To run a local server with a **local database**:
```
source servers/localhost/dev_local.env
uvicorn seqcolapi.main:app --reload --port 8100
```

To run a local server with **the production database**:
```
source servers/seqcolapi.databio.org/production.env
uvicorn seqcolapi.main:app --reload --port 8100
```

### Running with docker

To build the docker file:


```
docker build --no-cache -t scim .
```

To run in a container:

```
export POSTGRES_PASSWORD=`pass aws/rds_postgres` 
docker run --rm -p 8000:8000 --name sccon \
  --env "POSTGRES_PASSWORD" \
  --volume $CODE/seqcolapi.databio.org/config/seqcolapi.yaml:/config.yaml \
  scim seqcolapi serve -c /config.yaml -p 8000
```

To deploy container to dockerhub:

Use github action in this repo which deploys on release, or through manual dispatch.


Left to do:
- [x] it already retrieves from a refget server.
- [x] let me insert stuff using only checksums.
- [ ] make it take 2 refget servers correctly.


## To load new data into seqcolapi.databio.org

```
cd analysis
source ../servers/localhost/dev_local.env
ipython3
```

Now run `load_fasta.py`

## Deploy to AWS ECS

### Testing locally first

Build the seqcolapi image

```
cd
docker build -t docker.io/databio/seqcolapi:latest .
```

```
docker pull docker.io/databio/seqcolapi:latest
cd servers/seqcolapi.databio.org
docker build -t scim .
docker run \
  -e POSTGRES_HOST=$POSTGRES_HOST \
  -e POSTGRES_PASSWORD=$POSTGRES_PASSWORD \
  --network=host \
  scim
```

### Deploying

To upgrade the software:

Use config file located in `/servers/seqcolapi.databio.org`. This will use the image in docker.io://databio/seqcolapi, github repo: [refgenie/seqcolapi](https://github.com/refgenie/seqcolapi) as base, bundle it with the above config, and deploy to the shefflab ECS.

1. Ensure the [refget](https://github.com/refgenie/refget/) package master branch is as you want it.
2. Deploy the updated [secqolapi](https://github.com/refgenie/seqcolapi/) app to dockerhub (using manual dispatch, or deploy on github release).
3. Finally, deploy the instance with manual dispatch using the included GitHub action.


