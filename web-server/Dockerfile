# BASE INMAGE
FROM ubuntu:22.04

# INSTALL DEPENDENCIES & SOFTWARE
ARG DEBIAN_FRONTEND=noninteractive
ENV TZ=Europe/Madrid
RUN apt update && \
    apt install -y samtools libcurl4 libcurl4-openssl-dev bcftools default-jre wget curl tabix python3-pip gunicorn python3-gevent python3-pysam python3-requests git build-essential \
    libdbi-perl libdbd-mysql-perl libarchive-zip-perl libhttp-tiny-perl libwww-perl \
    libarchive-extract-perl libbz2-dev liblzma-dev zlib1g-dev libmodule-build-perl && \
    apt-get clean && \
    apt-get purge && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

#RUN pip install flask[async] httpx CrossMap
RUN pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org flask[async] httpx CrossMap  

# INSTALL VEP  
RUN git clone https://github.com/Ensembl/ensembl-vep.git && \
    cd ensembl-vep && \
    git checkout release/111 && \
    perl INSTALL.pl --AUTO a -s homo_sapiens -y GRCh37 && \
    cd ..

# DOWNLOAD PICARD
RUN mkdir -p /picard && wget -O /picard/picard.jar https://github.com/broadinstitute/picard/releases/download/2.25.1/picard.jar

# INSTALL BCFTOOLS +LIFTOVER
RUN wget https://github.com/samtools/bcftools/releases/download/1.20/bcftools-1.20.tar.bz2 && \
    tar xjvf /bcftools-1.20.tar.bz2 && \
    wget -O /bcftools-1.20/plugins/liftover.c https://github.com/freeseek/score/raw/master/liftover.c && \
    cd /bcftools-1.20 && make

ENV PATH="${PATH}:/bcftools-1.20"
ENV BCFTOOLS_PLUGINS="/bcftools-1.20/plugins"

COPY --chmod=755 ../docker-entrypoint.sh /docker-entrypoint/docker-entrypoint.sh
ENTRYPOINT ["/docker-entrypoint/docker-entrypoint.sh"]

# RUN FLASK APP
WORKDIR /app
#CMD gunicorn --workers=5 --bind 0.0.0.0:80 app:app
CMD FLASK_ENV=development flask run --host=0.0.0.0 --port 80 --reload 
