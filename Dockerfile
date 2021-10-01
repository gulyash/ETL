FROM python:3.9.6
WORKDIR /movies_admin

COPY movies_admin/requirements.txt movies_admin/dev-requirements.txt /movies_admin/
RUN pip install -r requirements.txt && pip install -r dev-requirements.txt

COPY movies_admin entrypoint.sh /movies_admin/
RUN chmod +x ./entrypoint.sh

ENTRYPOINT ["/movies_admin/entrypoint.sh"]
CMD ["standalone"]
# RE: "при старте сначала вызовет entrypoint, а потом CMD" -
# Во всех примерах, что я нашла, CMD содержит скорее аргумент по умолчанию для
# ENTRYPOINT-скрипта, чем полноценную команду, выполняемую после. Это и подразумевалось?
# Как лучше назвать "аргумент переключения" (CMD) между раздачей и нераздачей статики?
# Есть ли хорошие примеры ENTRYPOINT-скриптов с гайдлайнами по их написанию?