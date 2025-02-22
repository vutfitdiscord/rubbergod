FROM python:3.13-alpine3.21

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV TZ=Europe/Prague

# cairo - /room - for generating images
# git - setting bot presence and it's commit
# openssh - ios cog & merlin access
RUN apk update && apk add git cairo openssh
# lxml python library dependencies
RUN apk add libxml2-dev libxslt-dev python3-dev

VOLUME /rubbergod
WORKDIR /rubbergod

RUN /usr/local/bin/python -m pip install --upgrade pip
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone
COPY . .
RUN git config --global --add safe.directory /rubbergod

ENTRYPOINT [ "python3", "main.py" ]
