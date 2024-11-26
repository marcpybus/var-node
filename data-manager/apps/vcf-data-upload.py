#!/usr/bin/env python3

import psycopg
import pysam
import sys
import os
import time
import json 

from psycopg.rows import dict_row

genome = sys.argv[1]
vcf_file = sys.argv[2]

user = os.environ['POSTGRES_USER']
password = os.environ['POSTGRES_PASSWORD']
db = os.environ['POSTGRES_DB']
genotypes_per_insert = 1000000

# FUNCTIONS
def insert_genotypes(data, count_lines, contig, pos, genotypes_per_insert ):
    print(" - Inserting " + str(genotypes_per_insert) + " genotypes to database... " + str(count_lines) + " entries processed... please wait... (" + str(contig) + "-" + str(pos) + ") (" + str( round(time.time()) ) + " unix-time)", file=sys.stderr)
    try:
        conn = psycopg.connect(
            user=user,
            password=password,
            host="postgres",
            dbname=db,
            autocommit=True )
    except psycopg.Error as e:
        print(f"Error connecting to the database: {e}", file=sys.stderr)
        sys.exit(1)
    cur = conn.cursor() 
    try:
        cur.executemany("INSERT INTO vcf_genotypes ( genome, contig, pos, ref, alt, sample, zigosity, genotype_data ) VALUES ( %s, %s, %s, %s, %s, %s, %s, %s )", data) 
    except psycopg.Error as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    print(" --> done correctly! please wait..", file=sys.stderr)


# WORKFLOW

print("", file=sys.stderr)
print("Inserting " + genome + " genotypes to database...", file=sys.stderr)
try:
    conn = psycopg.connect(
        user=user,
        password=password,
        host="postgres",
        dbname=db,
        autocommit=True )
except psycopg.Error as e:
    print(f"Error connecting to the database: {e}", file=sys.stderr)
    sys.exit(1)
cur = conn.cursor() 
try:
    cur.execute("INSERT INTO available_genomes (genome) VALUES (%s) ON CONFLICT (genome) DO NOTHING;", [genome] )
except psycopg.Error as e:
    print(f"Error: {e}", file=sys.stderr)
    sys.exit(1)

file = pysam.VariantFile(vcf_file)
all_samples = list(file.header.samples)

try:
    conn = psycopg.connect(
        user=user,
        password=password,
        host="postgres",
        dbname=db,
        autocommit=True )
except psycopg.Error as e:
    print(f"Error connecting to the database: {e}", file=sys.stderr)
    sys.exit(1)

cur = conn.cursor( row_factory = dict_row ) 

for ref_sample in all_samples.copy():
    try:
            cur.execute( " SELECT sample FROM vcf_samples WHERE sample = %s AND genome = %s ", [ ref_sample, genome ] )
            for row in cur:
                existing_sample = row["sample"]
                all_samples.remove( existing_sample )
                print("", file=sys.stderr)
                print("ATTENTION! Sample " + existing_sample + " is already present in the " + genome + " database. UPLOAD WILL BE SKIPPED!", file=sys.stderr)
                print("  - Uploading genotypes from samples that already exists in the database is prohibited as it may lead to duplication of genotypes. ", file=sys.stderr)
                print("  - You should merge all the VCF files from the same sample into one, manually curate all duplicated genotypes and re-upload the resulting VCF file. You can do this with bcftools software ", file=sys.stderr)
                print("  - Before re-uploading the data you need remove this sample from the " + genome + " database using the following command: docker compose run -T data-manager remove-sample " + genome + " " + existing_sample + " ", file=sys.stderr)
    except psycopg.Error as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

print("", file=sys.stderr)
print("The following samples will be processed: " + str(all_samples), file=sys.stderr)
print("", file=sys.stderr)

print("Adding samples...", file=sys.stderr)
samples_data = []
for ref_sample in all_samples:
    samples_data.append( (genome,ref_sample) )
if( samples_data ):
    try:
        conn = psycopg.connect(
            user=user,
            password=password,
            host="postgres",
            dbname=db,
            autocommit=True )
    except psycopg.Error as e:
        print(f"Error connecting to the database: {e}", file=sys.stderr)
        sys.exit(1)
    cur = conn.cursor() 
    try:
        cur.executemany("INSERT INTO vcf_samples ( genome, sample ) VALUES ( %s, %s )", samples_data) 
    except psycopg.Error as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
else:
    print("There are no samples to add..", file=sys.stderr)
print("", file=sys.stderr)

print("Parsing genotypes...", file=sys.stderr)
data = []
count_records = 0
count_lines = 0
for record in file:
    if count_records >= genotypes_per_insert:
        insert_genotypes( data, count_lines, contig, pos, genotypes_per_insert )
        count_records = 0
        data = []
    count_lines += 1
    contig = record.contig
    pos = record.pos
    ref = record.ref
    for alt in record.alts:
        for sample in all_samples:
            if not "*" in record.samples[sample].alleles:
                if not None in record.samples[sample]["GT"]:
                    if alt in record.samples[sample].alleles:
                        zigosity = "HET"
                        if len(record.samples[sample]["GT"]) == 2:
                            if record.samples[sample]["GT"][0] == record.samples[sample]["GT"][1]:     
                                zigosity = "HOM"
                        elif len(record.samples[sample]["GT"]) == 1:
                            zigosity = "HEM"
                        else:
                            zigosity = "NA"
                        genotype_info = {}
                        for field, value in record.samples[sample].items():
                            genotype_info[field] = value
                        genotype_details = json.dumps(genotype_info)
                        if len(genotype_details) > 5000 or len(sample) > 50 or len(ref) > 1000 or len(alt) > 1000 or len(contig) > 2 or len(genome) > 6 or len(str(pos)) > 9:
                            print("\n Error. A parameter from the following record is too long for the table schema... skipping insertion...", file=sys.stderr)
                            print("   -->",genome,contig,pos,ref,alt,sample,zigosity,genotype_details, file=sys.stderr)
                        else:
                            count_records += 1
                            data.append( (genome,contig,pos,ref,alt,sample,zigosity,genotype_details) )

if data:
    print("Inserting last block of genotypes...", file=sys.stderr)
    insert_genotypes(data, count_lines, contig, pos, len(data) )

    print("Uploading of VCF genotypes has finished!", file=sys.stderr)
    print(" ", file=sys.stderr)
else:
    print("No VCF genotypes have been uploaded!", file=sys.stderr)
    print(" ", file=sys.stderr)
