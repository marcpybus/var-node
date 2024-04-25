#!/bin/bash

echo "Checking initial configuration..."
sleep 2

echo "Running Docker entrypoint..."
echo "Fetching VEP caches, Fasta files and liftOver chain files for GRCh37 and GRCh38 genomes (download size ~46Gb):"

echo " - GRCh37 fasta file... "
if [ ! -f /data/grch37/fasta/Homo_sapiens.GRCh37.dna.primary_assembly.fa.gz ] || [ $(wc -c /data/grch37/fasta/Homo_sapiens.GRCh37.dna.primary_assembly.fa.gz | cut -d' ' -f1) -ne 786207826 ]; then
    echo "    --> Downloading... "
    mkdir -p /data/grch37/fasta
    wget --no-verbose --show-progress --progress=dot:giga -O /data/grch37/fasta/Homo_sapiens.GRCh37.dna.primary_assembly.fa.gz  http://ftp.ensembl.org/pub/grch37/release-111/fasta/homo_sapiens/dna/Homo_sapiens.GRCh37.dna.primary_assembly.fa.gz
    gzip -d /data/grch37/fasta/Homo_sapiens.GRCh37.dna.primary_assembly.fa.gz
    bgzip /data/grch37/fasta/Homo_sapiens.GRCh37.dna.primary_assembly.fa
    samtools faidx /data/grch37/fasta/Homo_sapiens.GRCh37.dna.primary_assembly.fa.gz
fi
echo "    --> OK "

echo " - GRCh38 fasta file... "
if [ ! -f /data/grch38/fasta/Homo_sapiens.GRCh38.dna.primary_assembly.fa.gz ] || [ $(wc -c /data/grch38/fasta/Homo_sapiens.GRCh38.dna.primary_assembly.fa.gz | cut -d' ' -f1) -ne 797757362 ]; then
    echo "    --> Downloading... "
    mkdir -p /data/grch38/fasta
    wget --no-verbose --show-progress --progress=dot:giga -O /data/grch38/fasta/Homo_sapiens.GRCh38.dna.primary_assembly.fa.gz http://ftp.ensembl.org/pub/release-111/fasta/homo_sapiens/dna/Homo_sapiens.GRCh38.dna.primary_assembly.fa.gz
    gzip -d /data/grch38/fasta/Homo_sapiens.GRCh38.dna.primary_assembly.fa.gz
    bgzip /data/grch38/fasta/Homo_sapiens.GRCh38.dna.primary_assembly.fa
    samtools faidx /data/grch38/fasta/Homo_sapiens.GRCh38.dna.primary_assembly.fa.gz
fi
echo "    --> OK "

echo " - GRCh37 vep cache... "
if [ ! -d /data/grch37/vep_cache/homo_sapiens_merged ] || [ ! -f /data/grch37/vep_cache/homo_sapiens_merged_vep_111_GRCh37.tar.gz ] || [ $(wc -c /data/grch37/vep_cache/homo_sapiens_merged_vep_111_GRCh37.tar.gz | cut -d' ' -f1) -ne 19744068977 ]; then
    echo "    --> Downloading... "
    mkdir -p /data/grch37/vep_cache
    wget --no-verbose --show-progress --progress=dot:giga -O /data/grch37/vep_cache/homo_sapiens_merged_vep_111_GRCh37.tar.gz http://ftp.ensembl.org/pub/grch37/release-111/variation/indexed_vep_cache/homo_sapiens_merged_vep_111_GRCh37.tar.gz
    tar xzf /data/grch37/vep_cache/homo_sapiens_merged_vep_111_GRCh37.tar.gz -C /data/grch37/vep_cache/
    rm /data/grch37/vep_cache/homo_sapiens_merged_vep_111_GRCh37.tar.gz
fi
echo "    --> OK "

echo " - GRCh38 vep cache... "
if [ ! -d /data/grch38/vep_cache/homo_sapiens_merged ] || [ ! -f /data/grch38/vep_cache/homo_sapiens_merged_vep_111_GRCh38.tar.gz ] || [ $(wc -c /data/grch38/vep_cache/homo_sapiens_merged_vep_111_GRCh38.tar.gz | cut -d' ' -f1) -ne 27244793423 ]; then
    echo "    --> Downloading... "
    mkdir -p /data/grch38/vep_cache
    wget --no-verbose --show-progress --progress=dot:giga -O /data/grch38/vep_cache/homo_sapiens_merged_vep_111_GRCh38.tar.gz http://ftp.ensembl.org/pub/release-111/variation/indexed_vep_cache/homo_sapiens_merged_vep_111_GRCh38.tar.gz
    tar xzf /data/grch38/vep_cache/homo_sapiens_merged_vep_111_GRCh38.tar.gz -C /data/grch38/vep_cache/
    rm /data/grch38/vep_cache/homo_sapiens_merged_vep_111_GRCh38.tar.gz
fi
echo "    --> OK "

echo " - GRCh37 to GRCh38 chain... "
if [ ! -f /data/liftover/GRCh37_to_GRCh38.chain.gz ] || [ $(wc -c /data/liftover/GRCh37_to_GRCh38.chain.gz | cut -d' ' -f1) -ne 285250 ]; then
    echo "    --> Downloading... "
    mkdir -p /data/liftover
    wget --no-verbose --show-progress --progress=dot:giga -O /data/liftover/GRCh37_to_GRCh38.chain.gz http://ftp.ensembl.org/pub/assembly_mapping/homo_sapiens/GRCh37_to_GRCh38.chain.gz
fi
echo "    --> OK "

echo " - GRCh38 to GRCh37 chain... "
if [ ! -f /data/liftover/GRCh38_to_GRCh37.chain.gz ] || [ $(wc -c /data/liftover/GRCh38_to_GRCh37.chain.gz | cut -d' ' -f1) -ne 730394 ]; then
    echo "    --> Downloading... "
    mkdir -p /data/liftover
    wget --no-verbose --show-progress --progress=dot:giga -O /data/liftover/GRCh38_to_GRCh37.chain.gz http://ftp.ensembl.org/pub/assembly_mapping/homo_sapiens/GRCh38_to_GRCh37.chain.gz
fi
echo "    --> OK "

echo "Configuration finished correctly..."
exec "$@"
