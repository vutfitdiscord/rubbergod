FROM python:3.7-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

VOLUME /rubbergod
WORKDIR /rubbergod
COPY . .

RUN apt-get update && apt-get install -y git
RUN pip install -r requirements.txt --user
