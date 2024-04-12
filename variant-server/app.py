from werkzeug.middleware.proxy_fix import ProxyFix
from flask import Flask
from flask import render_template
import os
import pysam
import json
import csv
import sys
import mysql.connector

app = Flask( __name__ )
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_host=1, x_port=1, x_proto=1, x_prefix=1)

password = os.environ['MARIADB_ROOT_PASSWORD']
db = os.environ['MARIADB_DATABASE']

def get_genomes():
    try:
        conn = mysql.connector.connect( user="root", password=password, host="mariadb", port=3306, database=db )
    except mysql.connector.Error as e:
        print(f"Error connecting to MariaDB Platform: {e}")
        sys.exit(1)
    cur = conn.cursor(dictionary=True)
    cur.execute(" SELECT genome FROM available_genomes ")
    result = []
    for row in cur:
        result.append(row["genome"])
    cur.close()
    conn.close()
    return result


# ROUTES
@app.route('/info')
def show_node_data():
    output = {}
    output["database_genomes"] = get_genomes()
    output["error"] = "Ready"
    return json.dumps(output)

@app.route('/<string:genome>/<string:variant_id>')
def show_variant_id_data(genome, variant_id):

    output = {}
    database_genomes = get_genomes()
    output["database_genomes"] = database_genomes
    output["variant_id"] = variant_id
    output["samples"] = []

    if genome in database_genomes:

        chromosome  = variant_id.split("-")[0]
        position  = int(variant_id.split("-")[1])
        reference  = variant_id.split("-")[2]
        alternative  = variant_id.split("-")[3]

        sample_data = []
        try:
            conn = mysql.connector.connect( user="root", password=password, host="mariadb", port=3306, database=db )
        except mysql.connector.Error as e:
            print(f"Error connecting to MariaDB Platform: {e}")
            sys.exit(1)
        cur = conn.cursor(dictionary=True)
        cur.execute(" SELECT * FROM vcf_genotypes WHERE genome = '%s' AND contig = '%s' AND pos = %d AND ref = '%s' AND alt = '%s' ORDER BY RAND()" % (genome,chromosome,position,reference,alternative))
        homozygotes = 0
        heterozygotes = 0
        allele_count = 0
        for row in cur:
            if row["zigosity"] == "HOM":
                homozygotes += 1
                allele_count += 2
            if row["zigosity"] == "HET":
                heterozygotes += 1
                allele_count += 1
            sample_data.append(row)
        cur.close()
        conn.close()

        output["error"] = "OK"
        output["genome"] = genome
        output["homozygotes"] = homozygotes
        output["heterozygotes"] = heterozygotes
        output["allele_count"] = allele_count
        output["samples"] = sample_data[0 : 50]
    else:
        output["error"] = "Reference genome not found"
    #print(output, file=sys.stderr)
    return json.dumps(output)
