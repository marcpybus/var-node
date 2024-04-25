# BASE INMAGE
FROM ubuntu:22.04

# INSTALL DEPENDENCIES & SOFTWARE
ARG DEBIAN_FRONTEND=noninteractive
ENV TZ=Europe/Madrid
RUN apt update && \
    apt install -y wget tabix samtools python3 python3-pip \
    libmariadb-dev liblzma-dev libbz2-dev zlib1g-dev libcurl4-openssl-dev && \
    apt-get clean && \
    apt-get purge && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

#RUN pip install mariadb
RUN pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org mariadb pysam

RUN wget https://github.com/samtools/bcftools/releases/download/1.20/bcftools-1.20.tar.bz2 && \
    tar xjvf /bcftools-1.20.tar.bz2 && \
    wget -O /bcftools-1.20/plugins/liftover.c https://github.com/freeseek/score/raw/master/liftover.c && \
    cd /bcftools-1.20 && make

ENV PATH="${PATH}:/bcftools-1.20"
ENV BCFTOOLS_PLUGINS="/bcftools-1.20/plugins"
ENV PATH="${PATH}:/apps"

COPY --chmod=755 ./docker-entrypoint.sh /docker-entrypoint.sh
CMD ["/bin/bash", "/docker-entrypoint.sh"]
