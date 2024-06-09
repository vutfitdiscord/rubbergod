FROM python:3.12-alpine3.19

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV TZ=Europe/Prague

RUN apk update && apk add gcc git postgresql-dev musl-dev tzdata libxml2-dev libxslt-dev g++ openssh python3-dev graphviz-dev graphviz
RUN apk add jpeg-dev zlib-dev freetype-dev lcms2-dev openjpeg-dev tiff-dev tk-dev tcl-dev libwebp-dev libffi-dev cairo

VOLUME /rubbergod
WORKDIR /rubbergod

RUN /usr/local/bin/python -m pip install --upgrade pip
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt --user
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone
COPY . .
RUN git config --global --add safe.directory /rubbergod

ENTRYPOINT [ "python3", "main.py" ]
