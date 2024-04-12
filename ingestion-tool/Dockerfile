# BASE INMAGE
FROM ubuntu:22.04

# INSTALL DEPENDENCIES & SOFTWARE
ARG DEBIAN_FRONTEND=noninteractive
ENV TZ=Europe/Madrid
RUN apt update && \
    apt install -y tabix samtools bcftools libmariadb-dev python3-pip python3-pysam build-essential python3-mysqldb python3-mysql.connector python3-sqlalchemy \
    libdbi-perl libdbd-mysql-perl libarchive-zip-perl libhttp-tiny-perl libwww-perl \
    libarchive-extract-perl libbz2-dev liblzma-dev zlib1g-dev libmodule-build-perl && \
    apt-get clean && \
    apt-get purge && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

#RUN pip install mariadb
RUN pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org mariadb

#COPY --chmod=755 ./grch37-vcf-ingestion /apps/grch37-vcf-ingestion
#COPY --chmod=755 ./grch38-vcf-ingestion /apps/grch38-vcf-ingestion
#COPY --chmod=755 ./vcf-ingestion /apps/vcf-ingestion
#COPY --chmod=755 ./db-reset /apps/db-reset
ENV PATH="${PATH}:/apps"

CMD ["sh", "-c", "tail -f /dev/null"]
