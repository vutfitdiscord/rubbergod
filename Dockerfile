FROM python:3.8-alpine

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV TZ=Europe/Prague

RUN apk update && apk add gcc git postgresql-dev musl-dev tzdata libxml2-dev libxslt-dev g++
RUN apk add jpeg-dev zlib-dev freetype-dev lcms2-dev openjpeg-dev tiff-dev tk-dev tcl-dev libwebp-dev libffi-dev cairo

VOLUME /rubbergod
WORKDIR /rubbergod

RUN /usr/local/bin/python -m pip install --upgrade pip
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt --user
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone
COPY . .

ENTRYPOINT [ "python3", "rubbergod.py" ]
