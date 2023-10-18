# BASE INMAGE
FROM ubuntu:22.04

# INSTALL DEPENDENCIES & SOFTWARE
ARG DEBIAN_FRONTEND=noninteractive
ENV TZ=Europe/Madrid
RUN apt update && \
    apt install -y python3-flask gunicorn python3-gevent tabix && \
    apt-get clean && \
    apt-get purge && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# RUN FLASK APP
WORKDIR /api
CMD gunicorn --workers=2 --threads=2 --worker-connections=100 --reload --bind 0.0.0.0:5000 --worker-class gevent wgsi:app
