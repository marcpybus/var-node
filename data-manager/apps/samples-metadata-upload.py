#!/usr/bin/env python3

import psycopg
import pysam
import sys
import os
import time
import json 

from psycopg.rows import dict_row

tsv_file = sys.argv[1]

user = os.environ['POSTGRES_USER']
password = os.environ['POSTGRES_PASSWORD']
db = os.environ['POSTGRES_DB']

# WORKFLOW

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

f = open(tsv_file, "r")
header = f.readline().strip().split("\t")
for line in f:
    list = line.strip().split("\t")
    sample = list[0]
    metadata = {}
    for i in range(1, len(header)):
        if 0 <= i < len(list):
            metadata[header[i]] = list[i]
    try:
        cur.execute(" UPDATE vcf_samples SET sample_details = %s WHERE sample = %s ", ( json.dumps(metadata), sample ) ) 
        print(sample, metadata, file=sys.stderr)
    except psycopg.Error as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
print(f"Metadata upoloaded..", file=sys.stderr)

