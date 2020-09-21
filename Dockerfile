FROM python:3.8-buster

ENV TZ Europe/Moscow
    POETRY_NO_INTERACTION=1

RUN pip install --no-cache-dir --quiet --upgrade pip poetry

COPY ./bssapi /app/bssapi
COPY ./pyproject.toml /app/

WORKDIR /app
ENV PYTHONPATH=${PYTHONPATH}:${PWD}

RUN poetry config virtualenvs.create true \
    && poetry config virtualenvs.create false \
    && poetry config --unset virtualenvs.in-project \
    && poetry config --unset virtualenvs.path \
    && poetry config cache-dir "/tmp/poetry/cache" \
    && poetry install --no-dev \
    && poetry completions bash > /etc/bash_completion.d/poetry.bash-completion \
    && apt-get -yqq update && apt-get -yqq install mc bash-completion

STOPSIGNAL SIGINT
EXPOSE 8000/tcp
CMD ["bapi"]