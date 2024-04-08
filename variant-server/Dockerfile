# BASE INMAGE
FROM ubuntu:22.04

# INSTALL DEPENDENCIES & SOFTWARE
ARG DEBIAN_FRONTEND=noninteractive
ENV TZ=Europe/Madrid
RUN apt update && \
    apt install -y python3-pip gunicorn python3-gevent python3-pysam python3-requests git build-essential python3-mysqldb python3-mysql.connector \
    libdbi-perl libdbd-mysql-perl libarchive-zip-perl libhttp-tiny-perl libwww-perl \
    libarchive-extract-perl libbz2-dev liblzma-dev zlib1g-dev libmodule-build-perl && \
    apt-get clean && \
    apt-get purge && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

RUN pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org flask[async] httpx

# RUN FLASK APP
WORKDIR /app
#CMD gunicorn --workers=5 --bind 0.0.0.0:80 app:app
CMD FLASK_ENV=development flask run --host=0.0.0.0 --port 80 --reload 
