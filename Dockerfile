FROM python:3.9.6
WORKDIR /movies_admin

COPY movies_admin/requirements.txt movies_admin/dev-requirements.txt /movies_admin/
RUN pip install -r requirements.txt && pip install -r dev-requirements.txt

COPY movies_admin entrypoint.sh /movies_admin/
RUN chmod +x ./entrypoint.sh

ENTRYPOINT ["/movies_admin/entrypoint.sh"]
CMD ["standalone"]