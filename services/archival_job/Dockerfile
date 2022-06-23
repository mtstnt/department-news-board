FROM python:3.10.5-alpine3.16
WORKDIR /code
RUN pip install schedule requests
COPY . .
CMD ["python3", "main.py"]