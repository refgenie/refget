FROM tiangolo/uvicorn-gunicorn:python3.8-slim
LABEL authors="Nathan Sheffield"

COPY . /app
RUN pip install https://github.com/refgenie/refget/archive/dev.zip
RUN pip install https://github.com/databio/yacman/archive/dev.zip
RUN pip install .

