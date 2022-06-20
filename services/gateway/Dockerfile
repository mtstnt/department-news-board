FROM python:3.10.5-alpine3.16
WORKDIR /code

COPY requirements.txt requirements.txt

RUN apk add --no-cache --virtual .build-deps gcc musl-dev libffi-dev \
    && pip install --no-cache-dir -r /code/requirements.txt \
    && apk del .build-deps

COPY . .
CMD ["nameko", "run", "--config", "config.yml", "main"]