from werkzeug.middleware.proxy_fix import ProxyFix
from flask import Flask
from flask import render_template
from flask import redirect
import sys
import os
import httpx
import json
import asyncio
import tempfile
import subprocess
import re

NODES = '/network-configuration/nodes.json'
TIMEOUT = int(os.environ['QUERY_TIMEOUT'])
USE_VEP = int(os.environ['USE_VEP'])
CERT = '/network-configuration/' + os.environ['CLIENT_CERT_FILENAME']
KEY = '/network-configuration/' + os.environ['CLIENT_KEY_FILENAME']
CACERT = '/network-configuration/' + os.environ['CLIENT_CA_CERT_FILENAME']

NETWORK_NAME = os.environ['NETWORK_NAME']
NODE_NAME = os.environ['NODE_NAME']

SUPPORTED_CHROMOSOMES = {
    "chr1": "1",    "chr2": "2",    "chr3": "3",    "chr4": "4",    "chr5": "5",
    "chr6": "6",    "chr7": "7",    "chr8": "8",    "chr9": "9",    "chr10": "10",
    "chr11": "11",  "chr12": "12",  "chr13": "13",  "chr14": "14",  "chr15": "15",
    "chr16": "16",  "chr17": "17",  "chr18": "18",  "chr19": "19",  "chr20": "20",
    "chr21": "21",  "chr22": "22",  "chrX": "X",    "chrY": "Y",    "chrM": "MT"
}

SUPPORTED_GENOMES = {
    "grch37":{
        "cache":"/data/grch37/vep_cache",
        "fasta":"/data/grch37/fasta/Homo_sapiens.GRCh37.dna.primary_assembly.fa.gz",
        "assembly": "GRCh37",
        "liftover_chain": "/data/liftover/GRCh37_to_GRCh38.chain.gz"
        },
    "grch38":{
        "cache":"/data/grch38/vep_cache",
        "fasta":"/data/grch38/fasta/Homo_sapiens.GRCh38.dna.primary_assembly.fa.gz",
        "assembly": "GRCh38",
        "liftover_chain": "/data/liftover/GRCh38_to_GRCh37.chain.gz"
        }
    }

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_host=1, x_port=1, x_proto=1, x_prefix=1)
app.config["TEMPLATES_AUTO_RELOAD"] = True

# FUNCTIONS

def validate_genome_format(variant_id_data):
    if variant_id_data["genome"] not in SUPPORTED_GENOMES.keys():
        variant_id_data["validation"] = "Incorrect reference genome"
    return variant_id_data

def uscs_to_grch_chromosomes(variant_id_data):
    if variant_id_data["chromosome"] in SUPPORTED_CHROMOSOMES.values():
        variant_id_data["chromosome"] = variant_id_data["chromosome"]
    elif variant_id_data["chromosome"] in SUPPORTED_CHROMOSOMES.keys():
        variant_id_data["chromosome"] = SUPPORTED_CHROMOSOMES[ variant_id_data["chromosome"] ]
    else:
        variant_id_data["validation"] = "Incorrect assembled chromosome"
    return variant_id_data

def validate_variant_id_format( variant_id_data ):
    if re.findall("^(\w+)-(\d+)-([ACTG]+)-([ACTG]+)$", variant_id_data["variant_id"]):
        variant_id_list = variant_id_data["variant_id"].split("-")
        variant_id_data["chromosome"] = variant_id_list[0]
        variant_id_data["position"] = variant_id_list[1]
        variant_id_data["reference"] = variant_id_list[2]
        variant_id_data["alternative"] = variant_id_list[3]
    else:
        variant_id_data["validation"] = "Incorrect variant_id format"
    return variant_id_data

def variant_id_normalization(variant_id_data):
    with tempfile.TemporaryDirectory() as temp_dir:
        with open(temp_dir + "/input.vcf", 'w') as f:
            f.write("##fileformat=VCFv4.2\n##FORMAT=<ID=GT,Number=1,Type=String,Description='Genotype'>\n##contig=<ID="+variant_id_data["chromosome"]+",length=10000000000>\n#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\tSAMPLE\n"+variant_id_data["chromosome"]+"\t"+variant_id_data["position"]+"\t.\t"+variant_id_data["reference"]+"\t"+variant_id_data["alternative"]+"\t.\tPASS\t.\tGT\t0/1")
            f.close()
        output = subprocess.run(['/bcftools-1.20/bcftools','norm','--fasta-ref',SUPPORTED_GENOMES[variant_id_data["genome"]]["fasta"],'--check-ref','wx', temp_dir + "/input.vcf"], capture_output=True, text=True, )
        if "REF_MISMATCH" in output.stderr:
            for line in output.stderr.split("\n"):
                if line.startswith("REF_MISMATCH"):
                    variant_id_data["validation"] = line.replace("\t"," ")
        else:
            for line in output.stdout.split("\n"):
                if line.startswith(variant_id_data["chromosome"]):
                    vcf_line_list = line.split("\t")
                    variant_id_data["chromosome"] = vcf_line_list[0]
                    variant_id_data["position"] = vcf_line_list[1]
                    variant_id_data["reference"] = vcf_line_list[3]
                    variant_id_data["alternative"] = vcf_line_list[4]
        return variant_id_data

def variant_id_annotation(variant_id_data):
    if USE_VEP:
        vcf_input = variant_id_data["chromosome"] + " " + variant_id_data["position"] + " . " + variant_id_data["reference"] + " " + variant_id_data["alternative"] + " PASS ."
        output = subprocess.run(["/ensembl-vep/vep","--dont_skip","--cache","--offline","--dir_cache",SUPPORTED_GENOMES[variant_id_data["genome"]]["cache"],"--fasta",SUPPORTED_GENOMES[variant_id_data["genome"]]["fasta"],"--assembly",SUPPORTED_GENOMES[variant_id_data["genome"]]["assembly"],"--merged","--transcript_version","--hgvs","--hgvsg","--vcf","-input_data",vcf_input,"-o","STDOUT","--no_stats","--quiet","--warning_file","STDERR","--skipped_variants_file","STDERR"], capture_output=True, text=True)
        vcf = output.stdout
        for vcf_line in vcf.splitlines():
            if not vcf_line.startswith("#"):
                print( vcf_line , file=sys.stderr)
                vcf_list = vcf_line.split("\t")
                chr = vcf_list[0]
                pos = vcf_list[1]
                ref = vcf_list[3]
                alt = vcf_list[4]
                variant_id_data["variant_id"] = chr + "-" + pos + "-" + ref + "-" + alt
                variant_id_data["genome"] = variant_id_data["genome"]
                variant_id_data["results"] = []
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
                    variant_id_data["results"].append(tx_data)
    else:
        variant_id_data["results"]=[{"impact":"","consequence":"","internal_id":"VEP not enabled"}]
        print(variant_id_data, file=sys.stderr)
    print(USE_VEP, file=sys.stderr)
    return variant_id_data

def make_lift_over(variant_id_data):
    if( variant_id_data["genome"] == "grch37" ):
        variant_id_data["new_genome"] = "grch38"
    elif( variant_id_data["genome"] == "grch38" ):
        variant_id_data["new_genome"] = "grch37"
    else:
        variant_id_data["validation"] = "Incorrect reference genome at liftover" 
    if variant_id_data["new_genome"]:
        with tempfile.TemporaryDirectory() as temp_dir:
            with open(temp_dir + "/input.vcf", 'w') as f:
                f.write("##fileformat=VCFv4.2\n##FORMAT=<ID=GT,Number=1,Type=String,Description='Genotype'>\n##contig=<ID="+variant_id_data["chromosome"]+",length=10000000000>\n#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\tSAMPLE\n"+variant_id_data["chromosome"]+"\t"+variant_id_data["position"]+"\t.\t"+variant_id_data["reference"]+"\t"+variant_id_data["alternative"]+"\t.\tPASS\t.\tGT\t0/1")
                f.close()
            output = subprocess.run(["/bcftools-1.20/bcftools","+liftover",temp_dir + "/input.vcf","--","-s",SUPPORTED_GENOMES[variant_id_data["genome"]]["fasta"],"-f",SUPPORTED_GENOMES[variant_id_data["new_genome"]]["fasta"],"-c",SUPPORTED_GENOMES[variant_id_data["genome"]]["liftover_chain"]], capture_output=True, text=True)
            if "Error" in output.stderr:
                for line in output.stderr.split("\n"):
                    if line.startswith("Error"):
                        variant_id_data["validation"] = line.replace("\t"," ")
            else:
                for line in output.stdout.split("\n"):
                    if line.startswith(variant_id_data["chromosome"]):
                        vcf_line_list = line.split("\t")
                        variant_id_data["new_chromosome"] = vcf_line_list[0]
                        variant_id_data["new_position"] = vcf_line_list[1]
                        variant_id_data["new_reference"] = vcf_line_list[3]
                        variant_id_data["new_alternative"] = vcf_line_list[4]
                        variant_id_data["new_variant_id"] = variant_id_data["new_chromosome"] + "-" + variant_id_data["new_position"] + "-" + variant_id_data["new_reference"] + "-" + variant_id_data["new_alternative"]
    return variant_id_data

async def make_request(session, node, genome, variant_id):
    if genome and variant_id:
        url = 'https://' + node["node_host"] + ':' + node["node_port"] + '/' + genome + '/' + variant_id
    else:
        url = 'https://' + node["node_host"] + ':' + node["node_port"] + '/info'
    return await session.get( url )

async def get_data_from_nodes(genome, variant_id):
    data = []
    with open(NODES) as json_file:
        nodes = json.load(json_file)
    #async with httpx.AsyncClient( timeout = TIMEOUT, verify=CACERT,cert=(CERT, KEY)) as session:
    async with httpx.AsyncClient( timeout = TIMEOUT, verify=False, cert=(CERT, KEY) ) as session:
        tasks = [make_request(session, node, genome, variant_id) for node in nodes]
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        print(responses, file=sys.stderr)
        for idx,r in enumerate(responses):
            print(r.request.url, file=sys.stderr)
            print(r.request.headers, file=sys.stderr)
            node = {}
            node["node_name"] = nodes[idx]["node_name"]
            node["node_host"] = nodes[idx]["node_host"]
            node["node_port"] = nodes[idx]["node_port"]
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
    return render_template("base.html", variant_id_data = None, results = None, node_name = NODE_NAME, network_name = NETWORK_NAME )

@app.route('/info')
async def info(variant_id = '', genome = ''):
    results = await get_data_from_nodes(genome, variant_id)
    return render_template("base.html", variant_id_data = {"variant_id":variant_id}, results = results, node_name = NODE_NAME, network_name = NETWORK_NAME )

@app.route('/<genome>/<variant_id>')
async def show_variant_id_results(genome, variant_id):
    results = {}
    variant_id_data = { "validation": "OK", "variant_id": variant_id, "genome": genome }
    variant_id_data = validate_genome_format(variant_id_data)
    if variant_id_data["validation"] == "OK":
        variant_id_data = validate_variant_id_format(variant_id_data)
        if variant_id_data["validation"] == "OK":
            uscs_to_grch_chromosomes(variant_id_data)
            if variant_id_data["validation"] == "OK":
                variant_id_data = variant_id_normalization(variant_id_data)
                if variant_id_data["validation"] == "OK":
                    variant_id_data = variant_id_annotation(variant_id_data)
                    if variant_id_data["validation"] == "OK":
                        results = await get_data_from_nodes(genome, variant_id)
    return render_template("base.html", variant_id_data = variant_id_data, results = results, node_name = NODE_NAME, network_name = NETWORK_NAME)
    
@app.route('/json/<genome>/<variant_id>')
async def show_variant_id_json(genome, variant_id):
    results = {}
    variant_id_data = { "validation": "OK", "variant_id": variant_id, "genome": genome }
    variant_id_data = validate_genome_format(variant_id_data)
    if variant_id_data["validation"] == "OK":
        variant_id_data = validate_variant_id_format(variant_id_data)
        if variant_id_data["validation"] == "OK":
            uscs_to_grch_chromosomes(variant_id_data)
            if variant_id_data["validation"] == "OK":
                variant_id_data = variant_id_normalization(variant_id_data)
                if variant_id_data["validation"] == "OK":
                    variant_id_data = variant_id_annotation(variant_id_data)
                    if variant_id_data["validation"] == "OK":
                        results = await get_data_from_nodes(genome, variant_id)
    return render_template("json.html", variant_id_data = variant_id_data, results = results, node_name = NODE_NAME, network_name = NETWORK_NAME)

@app.route('/liftover/<genome>/<variant_id>')
async def make_liftover(genome, variant_id):
    variant_id_data = { "validation": "OK", "variant_id": variant_id, "genome": genome }
    variant_id_data = validate_genome_format(variant_id_data)
    if variant_id_data["validation"] == "OK":
        variant_id_data = validate_variant_id_format(variant_id_data)
        if variant_id_data["validation"] == "OK":
            uscs_to_grch_chromosomes(variant_id_data)
            if variant_id_data["validation"] == "OK":
                variant_id_data = variant_id_normalization(variant_id_data)
                if variant_id_data["validation"] == "OK":
                    variant_id_data = make_lift_over(variant_id_data)
    if variant_id_data["validation"] == "OK":
        return redirect("/" + variant_id_data["new_genome"] + "/" + variant_id_data["new_variant_id"])
    else:
        return "Lift over error! " + variant_id_data["validation"]
    