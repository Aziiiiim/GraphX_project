FROM python:3.12

WORKDIR /app

COPY ./ingestor .
COPY ./api/utils ./utils
RUN pip install -r requirements.txt

ENV PYTHONPATH=/app:$PYTHONPATH
ENV PYTHONUNBUFFERED=1
CMD ["python", "main.py"]