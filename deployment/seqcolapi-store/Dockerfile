FROM tiangolo/uvicorn-gunicorn:python3.11-slim
LABEL authors="Nathan Sheffield"

# The store-backed service needs no database packages. `refget[seqcolapi]` pulls
# fastapi and uvicorn only, so sqlmodel, sqlalchemy and psycopg2 stay out of the
# image. The Postgres-backed service is a separate deployment and installs
# `refget[seqcolapi-db]`.
#
# seqcolapi now ships inside the refget wheel (refget/seqcolapi/), so there is
# nothing to COPY -- the app is importable straight from site-packages. gtars is
# a base dependency of refget and no longer needs its own install line.
RUN pip install --no-cache-dir \
    "refget[seqcolapi] @ https://github.com/refgenie/refget/archive/dev.zip"

CMD ["uvicorn", "refget.seqcolapi.main:store_app", "--host", "0.0.0.0", "--port", "80"]
