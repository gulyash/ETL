FROM python:3.9.6

ENV PYTHONUNBUFFERED=1
COPY . .
RUN pip install -r requirements.txt

CMD ["etl.py", "--log=INFO"]
ENTRYPOINT ["python3"]
