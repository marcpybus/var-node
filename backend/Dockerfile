# BASE INMAGE
FROM ubuntu:22.04

# INSTALL DEPENDENCIES & SOFTWARE
ARG DEBIAN_FRONTEND=noninteractive
ENV TZ=Europe/Madrid
RUN apt update && \
    apt install -y wget curl tabix python3-pip gunicorn python3-gevent python3-pysam python3-requests git build-essential \
    libdbi-perl libdbd-mysql-perl libarchive-zip-perl libhttp-tiny-perl libwww-perl \
    libarchive-extract-perl libbz2-dev liblzma-dev zlib1g-dev libmodule-build-perl && \
    apt-get clean && \
    apt-get purge && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

#RUN pip install flask[async] httpx
RUN pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org flask[async] httpx CrossMap  

# INSTALL VEP  
RUN git clone https://github.com/Ensembl/ensembl-vep.git && \
    cd ensembl-vep && \
    git checkout release/111 && \
    perl INSTALL.pl --AUTO a -s homo_sapiens -y GRCh37 && \
    cd ..

COPY --chmod=755 ../docker-entrypoint.sh /docker-entrypoint/docker-entrypoint.sh
ENTRYPOINT ["/docker-entrypoint/docker-entrypoint.sh"]

# RUN FLASK APP
WORKDIR /flask-app
#CMD gunicorn --workers=5 --bind 0.0.0.0:80 app:app
CMD FLASK_ENV=development flask run --host=0.0.0.0 --port 80 --reload 
