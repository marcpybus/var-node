# BASE INMAGE
FROM ubuntu:22.04

# INSTALL DEPENDENCIES & SOFTWARE
ARG DEBIAN_FRONTEND=noninteractive
ENV TZ=Europe/Madrid
RUN apt update && \
    apt install -y python3 python3-pip gunicorn && \
    apt-get clean && \
    apt-get purge && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

RUN pip install flask[async] httpx "psycopg[binary,pool]"

# RUN FLASK APP
WORKDIR /app
CMD gunicorn --workers=5 --bind 0.0.0.0:80 app:app
#CMD FLASK_ENV=development flask run --host=0.0.0.0 --port 80 --reload 

