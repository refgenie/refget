FROM tiangolo/uvicorn-gunicorn:python3.11-slim
LABEL authors="Nathan Sheffield"
RUN pip install https://github.com/refgenie/refget/archive/dev.zip

COPY requirements/requirements-seqcolapi.txt requirements/requirements-seqcolapi.txt
RUN pip install -r requirements/requirements-seqcolapi.txt --no-cache-dir

COPY . /app/seqcolapi

CMD ["uvicorn", "seqcolapi.main:app", "--host", "0.0.0.0", "--port", "80"]
