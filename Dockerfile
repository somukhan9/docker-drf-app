FROM python:3.10-alpine
MAINTAINER SamRaT

ENV PYTHONUNBUFFERED 1

COPY ./requirements.txt /requirements.txt

RUN python3 -m pip install --upgrade pip

RUN pip install -r /requirements.txt

RUN mkdir /app
WORKDIR /app

COPY ./app /app

RUN adduser -D user
USER user