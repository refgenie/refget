FROM tiangolo/uvicorn-gunicorn:python3.11-slim
LABEL authors="Nathan Sheffield"
RUN pip install https://github.com/refgenie/refget/archive/dev.zip
RUN pip install gtars

COPY seqcolapi/ /app/seqcolapi

CMD ["uvicorn", "seqcolapi.main:store_app", "--host", "0.0.0.0", "--port", "80"]
