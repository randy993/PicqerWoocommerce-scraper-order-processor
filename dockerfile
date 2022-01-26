FROM python:3.7.3

WORKDIR /SlimmeheaterApp

COPY requirements.txt .
COPY ./app/config.json ./app/config.json
COPY ./app/gsheets-api.json ./app/gsheets-api.json

RUN pip install -r requirements.txt

COPY ./app ./app

CMD ["python", "./app/app.py"]