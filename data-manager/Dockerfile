# BASE INMAGE
FROM ubuntu:22.04

# INSTALL DEPENDENCIES & SOFTWARE
ARG DEBIAN_FRONTEND=noninteractive
ENV TZ=Europe/Madrid
RUN apt update && \
    apt install -y wget libcurl4 libcurl4-openssl-dev tabix samtools bcftools libmariadb-dev python3-pip python3-pysam build-essential python3-mysqldb python3-mysql.connector python3-sqlalchemy \
    libdbi-perl libdbd-mysql-perl libarchive-zip-perl libhttp-tiny-perl libwww-perl \
    libarchive-extract-perl libbz2-dev liblzma-dev zlib1g-dev libmodule-build-perl && \
    apt-get clean && \
    apt-get purge && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

#RUN pip install mariadb
RUN pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org mariadb

RUN wget https://github.com/samtools/bcftools/releases/download/1.20/bcftools-1.20.tar.bz2 && \
    tar xjvf /bcftools-1.20.tar.bz2 && \
    wget -O /bcftools-1.20/plugins/liftover.c https://github.com/freeseek/score/raw/master/liftover.c && \
    cd /bcftools-1.20 && make

ENV PATH="${PATH}:/bcftools-1.20"
ENV BCFTOOLS_PLUGINS="/bcftools-1.20/plugins"
ENV PATH="${PATH}:/apps"
