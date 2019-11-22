FROM ubuntu:16.04

MAINTAINER Roger Helkey "roger@helkey.org"

RUN apt-get update -y && \
    apt-get install -y python3-pip python3-dev

WORKDIR /

COPY ./server.py /
COPY ./garage.py /

ENTRYPOINT [ "python3" ]

CMD [ "server.py" ]