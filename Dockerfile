FROM python:3.8-buster

ENV TZ=Europe/Moscow \
    POETRY_NO_INTERACTION=1 \
    POETRY_NO_DEV=1 \
    PYTHONPATH=${PYTHONPATH}:/app \
    WEB_CONCURRENCY=4 \
    FORWARDED_ALLOW_IPS=*

RUN pip install --no-cache-dir --quiet --upgrade pip poetry \
    && poetry config virtualenvs.create true \
    && poetry config virtualenvs.create false \
    && poetry config --unset virtualenvs.in-project \
    && poetry config --unset virtualenvs.path \
    && poetry config cache-dir "/tmp/poetry/cache" \
    && apt-get -yqq update && apt-get -yqq install mc htop

WORKDIR /app
COPY ./bssapi /app/bssapi
COPY ./pyproject.toml /app/
RUN poetry update \
    && poetry install \
    && poetry completions bash > /etc/bash_completion.d/poetry.bash-completion


STOPSIGNAL SIGINT
EXPOSE 8000/tcp
CMD ["bapi"]