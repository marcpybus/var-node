# BASE INMAGE
FROM ubuntu:22.04

# INSTALL DEPENDENCIES & SOFTWARE
ARG DEBIAN_FRONTEND=noninteractive
ENV TZ=Europe/Madrid
RUN apt update && \
    apt install -y wget tabix samtools gunicorn git python3 python3-pip \
    libmariadb-dev liblzma-dev libbz2-dev zlib1g-dev libcurl4-openssl-dev \ 
    libdbi-perl libdbd-mysql-perl libarchive-zip-perl libhttp-tiny-perl libwww-perl libarchive-extract-perl libmodule-build-perl && \
    apt-get clean && \
    apt-get purge && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

#RUN pip install flask[async] httpx pysam
RUN pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org flask[async] httpx pysam

# INSTALL VEP  
RUN git clone https://github.com/Ensembl/ensembl-vep.git && \
    cd ensembl-vep && \
    git checkout release/111 && \
    perl INSTALL.pl --AUTO a -s homo_sapiens -y GRCh37 && \
    cd ..

# INSTALL BCFTOOLS +LIFTOVER
RUN wget https://github.com/samtools/bcftools/releases/download/1.20/bcftools-1.20.tar.bz2 && \
    tar xjvf /bcftools-1.20.tar.bz2 && \
    wget -O /bcftools-1.20/plugins/liftover.c https://github.com/freeseek/score/raw/master/liftover.c && \
    cd /bcftools-1.20 && make

ENV PATH="${PATH}:/bcftools-1.20"
ENV BCFTOOLS_PLUGINS="/bcftools-1.20/plugins"

# RUN FLASK APP
WORKDIR /app
CMD gunicorn --workers=5 --bind 0.0.0.0:80 app:app
#CMD FLASK_ENV=development flask run --host=0.0.0.0 --port 80 --reload 
