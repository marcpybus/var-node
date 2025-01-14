from werkzeug.middleware.proxy_fix import ProxyFix
from flask_jwt_extended import jwt_required
from flask_jwt_extended import JWTManager
from flask_jwt_extended import get_jwt_identity
from flask import Flask, request
from flask import jsonify
from cryptography.fernet import Fernet
import os
import json
import sys
import psycopg
import base64
from psycopg.rows import dict_row

app = Flask( __name__ )
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_host=1, x_port=1, x_proto=1, x_prefix=1)
app.config["JWT_SECRET_KEY"] = os.environ['JWT_SECRET_KEY']  
jwt = JWTManager(app)

RESPONSE_ENCRYPTION = int(os.environ['RESPONSE_ENCRYPTION'])
JWT_SECRET_KEY = os.environ['JWT_SECRET_KEY']

user = os.environ['POSTGRES_USER']
password = os.environ['POSTGRES_PASSWORD']
db = os.environ['POSTGRES_DB']

node_name = os.environ['NODE_NAME']
contact_email = os.environ['CONTACT_EMAIL']

def get_genomes():
    try:
        conn = psycopg.connect( user=user, password=password, host="postgres", dbname=db )
    except psycopg.Error as e:
        print(f"Error connecting to Postgres Platform: {e}")
        sys.exit(1)
    cur = conn.cursor( row_factory = dict_row )
    cur.execute(" SELECT genome, num_samples, num_genotypes FROM available_genomes ")
    result = []
    for row in cur:
        result.append(row)
    cur.close()
    conn.close()
    return result

def encrypt_data(data):
    if RESPONSE_ENCRYPTION:
        code_bytes = JWT_SECRET_KEY.encode("utf-8")
        key = base64.urlsafe_b64encode(code_bytes.ljust(32)[:32])
        f = Fernet(key)
        encrypted_data = f.encrypt(data.encode())
        return encrypted_data
    else:
        return data

def decrypt_data(encrypted_data):
    if RESPONSE_ENCRYPTION:
        code_bytes = JWT_SECRET_KEY.encode("utf-8")
        key = base64.urlsafe_b64encode(code_bytes.ljust(32)[:32])
        f = Fernet(key)
        decrypted_data = f.decrypt(encrypted_data).decode()
        return decrypted_data
    else:
        return encrypted_data

# ROUTES
@app.route('/info')
@jwt_required()
def show_node_data():
    output = {}
    output["database_genomes"] = get_genomes()
    output["error"] = "Ready"
    return encrypt_data(json.dumps(output))

@app.route('/<string:genome>/<string:variant_id>')
@jwt_required()
def show_variant_id_data(genome, variant_id):
    
    print(dict(request.headers), file=sys.stderr)
    requesting_node = get_jwt_identity()
    #print("requesting node: " + requesting_node, file=sys.stderr)

    try:
        conn = psycopg.connect( user=user, password=password, host="postgres", dbname=db, autocommit=True)
    except psycopg.Error as e:
        print(f"Error connecting to postgres platform: {e}")
        sys.exit(1)
    cur = conn.cursor()
    try:
        cur.execute("INSERT INTO requesting_nodes ( node_name, requests ) VALUES ( %s, %s ) ON CONFLICT (node_name) DO UPDATE SET requests = requesting_nodes.requests + 1", [requesting_node,1]) 
    except psycopg.Error as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)    

    output = {}
    genomes_list = []
    database_genomes = get_genomes()
    for genome_entry in database_genomes:
        genomes_list.append(genome_entry["genome"])
    output["database_genomes"] = database_genomes
    output["variant_id"] = variant_id
    output["samples"] = []

    if genome in genomes_list:

        chromosome  = variant_id.split("-")[0]
        position  = int(variant_id.split("-")[1])
        reference  = variant_id.split("-")[2]
        alternative  = variant_id.split("-")[3]

        sample_data = []
        try:
            conn = psycopg.connect( user=user, password=password, host="postgres", dbname=db )
        except psycopg.Error as e:
            print(f"Error connecting to postgres platform: {e}")
            sys.exit(1)
        cur = conn.cursor( row_factory = dict_row )
        cur.execute(" SELECT vcf_genotypes.zigosity, vcf_genotypes.genotype_data, vcf_samples.sample_data FROM vcf_genotypes LEFT JOIN vcf_samples ON vcf_genotypes.sample = vcf_samples.sample AND vcf_genotypes.genome = vcf_samples.genome WHERE vcf_genotypes.genome = %s AND vcf_genotypes.contig = %s AND vcf_genotypes.pos = %s AND vcf_genotypes.ref = %s AND vcf_genotypes.alt = %s ORDER BY RANDOM()", (genome,chromosome,position,reference,alternative))
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
        output["node_name"] = node_name
        output["contact_email"] = contact_email
        output["homozygotes"] = homozygotes
        output["heterozygotes"] = heterozygotes
        output["allele_count"] = allele_count
        output["samples"] = sample_data[0 : 50]
    else:
        output["error"] = "Reference genome not found"
    #print(output, file=sys.stderr)
    return encrypt_data(json.dumps(output))
