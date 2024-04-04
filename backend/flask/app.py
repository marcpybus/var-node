from werkzeug.middleware.proxy_fix import ProxyFix
from flask import Flask
from flask import render_template
from flask import redirect
import sys
import requests
import httpx
import json
import asyncio
import tempfile
import time
import ssl
import subprocess
import re

CERT = '/network-config/cert.pem'
KEY = '/network-config/key.pem'
CACERT = '/network-config/ca-cert.pem'
NODES = '/network-config/nodes.json'
TIMEOUT = None
SUPPORTED_CHROMOSOMES = ["1","2","3","4","5","6","7","8","9","10","11","12","13","14","15","16","17","18","19","20","21","22","X","Y","MT"]
SUPPORTED_GENOMES = {
    "grch37":{
        "cache":"/data/grch37/vep_cache",
        "fasta":"/data/grch37/fasta/Homo_sapiens.GRCh37.dna.primary_assembly.fa.gz",
        "assembly": "GRCh37",
        "liftover": "/data/liftover/GRCh37_to_GRCh38.chain.gz"
        },
    "grch38":{
        "cache":"/data/grch38/vep_cache",
        "fasta":"/data/grch38/fasta/Homo_sapiens.GRCh38.dna.primary_assembly.fa.gz",
        "assembly": "GRCh38",
        "liftover": "/data/liftover/GRCh38_to_GRCh37.chain.gz"
        }
    }

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_host=1, x_port=1, x_proto=1, x_prefix=1)
app.config["TEMPLATES_AUTO_RELOAD"] = True

# FUNCTIONS

def make_lift_over(genome, variant_id):
    data = { "validation": "OK", "variant_id": variant_id }
    variant_id_list = variant_id.split("-")
    if len(variant_id_list) == 4:
        chromosome  = variant_id_list[0]
        position  = int(variant_id_list[1])
        reference  = variant_id_list[2]
        alternative  = variant_id_list[3]
        if reference == alternative:
            data["validation"] = "Same reference and alternative allele" 
        if not re.match('^[ACTG]+$',reference):
            data["validation"] = "Wrong reference allele format" 
        if not re.match('^[ACTG]+$',alternative):
            data["validation"] = "Wrong alternative allele format"  
        if position < 0 or position > 1000000000:
            data["validation"] = "Wrong position format or position number"  
        if chromosome not in SUPPORTED_CHROMOSOMES:
            data["validation"] = "Wrong chromosome format"   
        if genome not in SUPPORTED_GENOMES.keys():
            data["validation"] = "Wrong genome format"  
    else:
        data["validation"] = "Wrong variant_id format" 
    
    if( genome == "grch37" ):
        data["new_genome"] = "grch38"
    elif( genome == "grch38" ):
        data["new_genome"] = "grch37"
    else:
        data["validation"] = "Wrong reference genome" 

    if data["validation"] == "OK" :
        tempdir = tempfile.mkdtemp()
        with open(tempdir + "/input.bed", 'w') as f:
            f.write(chromosome + " " + str(position) + " " + str(position) + "\n")
            f.close()
        output = subprocess.run(["CrossMap","bed",SUPPORTED_GENOMES[genome]["liftover"],tempdir + "/input.bed","/dev/stdout"], capture_output=True, text=True)
        bed = output.stdout
        bed_list = bed.split("\t")
        data["new_variant_id"] = bed_list[0] + "-" + bed_list[1] + "-" + reference + "-" + alternative
    return data

def validate_variant_id(genome, variant_id):
    data = { "validation": "OK", "variant_id": variant_id }
    variant_id_list = variant_id.split("-")
    if len(variant_id_list) == 4:
        chromosome  = variant_id_list[0]
        position  = int(variant_id_list[1])
        reference  = variant_id_list[2]
        alternative  = variant_id_list[3]
        if reference == alternative:
            data["validation"] = "Same reference and alternative allele" 
        if not re.match('^[ACTG]+$',reference):
            data["validation"] = "Wrong reference allele format" 
        if not re.match('^[ACTG]+$',alternative):
            data["validation"] = "Wrong alternative allele format"  
        if position < 0 or position > 1000000000:
            data["validation"] = "Wrong position format or position number"  
        if chromosome not in SUPPORTED_CHROMOSOMES:
            data["validation"] = "Wrong chromosome format"   
        if genome not in SUPPORTED_GENOMES.keys():
            data["validation"] = "Wrong genome format"  
    else:
        data["validation"] = "Wrong variant_id format" 

    if data["validation"] == "OK" :
        vcf_input = chromosome + " " + str(position) + " . " + reference + " " + alternative + " PASS ."
        output = subprocess.run(["/ensembl-vep/vep","--dont_skip","--check_ref","--cache","--offline","--dir_cache",SUPPORTED_GENOMES[genome]["cache"],"--fasta",SUPPORTED_GENOMES[genome]["fasta"],"--assembly",SUPPORTED_GENOMES[genome]["assembly"],"--merged","--transcript_version","--hgvs","--hgvsg","--vcf","-input_data",vcf_input,"-o","STDOUT","--no_stats","--quiet"], capture_output=True, text=True)
        vcf = output.stdout
        for vcf_line in vcf.splitlines():
            if not vcf_line.startswith("#"):
                print( vcf_line , file=sys.stderr)
                vcf_list = vcf_line.split("\t")
                chr = vcf_list[0]
                pos = vcf_list[1]
                ref = vcf_list[3]
                alt = vcf_list[4]
                data["variant_id"] = chr + "-" + pos + "-" + ref + "-" + alt
                data["genome"] = genome
                data["results"] = []
                info_field = vcf_list[7]
                info_list = info_field[4:].split(",")
                for tx_info in info_list:
                    tx_data = {}
                    tx_info_list = tx_info.split("|")
                    gene = tx_info_list[3]
                    tx_id = tx_info_list[6]
                    if tx_info_list[30]:
                        hgvsc_list = tx_info_list[10].split(":")
                        hgvsc = ''
                        if len(hgvsc_list) > 1: hgvsc = hgvsc_list[1] 
                        hgvsp_list = tx_info_list[11].split(":")
                        hgvsp = ''
                        if len(hgvsp_list) > 1: hgvsp = hgvsp_list[1] 
                        hgvsg_list = tx_info_list[30].split(":")
                        hgvsg = ''
                        if len(hgvsg_list) > 1: hgvsg = hgvsg_list[1] 
                        if hgvsc == '': hgvsc = hgvsg
                        if gene:
                            internal_id =  gene + "(" + tx_id + "):" + hgvsc
                        else:
                            internal_id =  tx_info_list[30]
                        if hgvsp != '': internal_id = internal_id + ":" + hgvsp
                        tx_data["internal_id"] = internal_id
                    if tx_info_list[1]:
                        tx_data["consequence"] = tx_info_list[1]
                    if tx_info_list[2]:
                        tx_data["impact"] = tx_info_list[2]
                    if tx_info_list[31] == "failed":
                        data["validation"] = "Incorrect reference allele at selected genome position"
                    else:
                        data["validation"] = "OK"
                        data["results"].append(tx_data)
    return data

async def make_request(session, node, genome, variant_id):
    if genome and variant_id:
        url = 'https://' + node["node_host"] + '/' + genome + '/' + variant_id
    else:
        url = 'https://' + node["node_host"] + '/info'
    return await session.get( url)

async def get_data_from_nodes(genome, variant_id):
    data = []
    with open(NODES) as json_file:
        nodes = json.load(json_file)
    async with httpx.AsyncClient( timeout = TIMEOUT, verify=CACERT,cert=(CERT, KEY)) as session:
        tasks = [make_request(session, node, genome, variant_id) for node in nodes]
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        print(responses, file=sys.stderr)
        for idx,r in enumerate(responses):
            node = {}
            node["node_name"] = nodes[idx]["node_name"]
            node["node_host"] = nodes[idx]["node_host"]
            node["database_genomes"] = []
            if hasattr(r,"status_code"):
                if r.status_code == httpx.codes.OK:
                    node.update( json.loads(r.text) )
                else:
                    node["error"] = r.status_code
            elif hasattr(r,"reason"):
                node["error"] = r.reason
            else:
                if str(r):
                    node["error"] = str(r)
                else:
                    node["error"] = "Unidentified error"
            data.append( node )
    return data

# ROUTES

@app.route('/')
async def index(variant_id = '', genome = ''):
    return render_template("base.html", variant_id_data = None, results = None )

@app.route('/info')
async def info(variant_id = '', genome = ''):
    results = await get_data_from_nodes(genome, variant_id)
    return render_template("base.html", variant_id_data = {"variant_id":variant_id}, results = results )

@app.route('/<genome>/<variant_id>')
async def show_variant_id_results(genome, variant_id):
    variant_id = variant_id.replace("chr","")
    variant_id_data = validate_variant_id(genome, variant_id)
    if variant_id_data["validation"] == "OK":
        results = await get_data_from_nodes(genome, variant_id)
    else:
        results = {}
    return render_template("base.html", variant_id_data = variant_id_data, results = results)
    
@app.route('/json/<genome>/<variant_id>')
async def show_variant_id_json(genome, variant_id):
    variant_id = variant_id.replace("chr","")
    variant_id_data = validate_variant_id(genome, variant_id)
    if variant_id_data["validation"] == "OK":
        results = await get_data_from_nodes(genome, variant_id)
    else:
        results = {}
    return render_template("json.html", variant_id_data = variant_id_data, results = results)

@app.route('/liftover/<genome>/<variant_id>')
async def make_liftover(genome, variant_id):
    variant_id = variant_id.replace("chr","")
    lift_over_data = make_lift_over(genome, variant_id)
    if lift_over_data["validation"] == "OK":
        return redirect("/" + lift_over_data["new_genome"] + "/" + lift_over_data["new_variant_id"])
    else:
        return "Lift over error! " + lift_over_data["validation"]
    