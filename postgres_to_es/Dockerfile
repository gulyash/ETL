FROM python:3.9.6-slim

ENV PYTHONUNBUFFERED=1

WORKDIR src
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt --no-cache-dir
COPY . .

CMD ["python3", "etl.py"]
