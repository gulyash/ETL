FROM python:3.9.6

ENV PYTHONUNBUFFERED=1

WORKDIR src
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt
COPY . .

CMD ["python3", "etl.py"]
