FROM python:3.8-buster

ENV TZ=Europe/Moscow \
    WEB_CONCURRENCY=4 \
    FORWARDED_ALLOW_IPS=*

RUN pip install --no-cache-dir --quiet --upgrade pip bssapi

STOPSIGNAL SIGINT
EXPOSE 8000/tcp
CMD ["bapi"]