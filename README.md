# xicvar-node

*xicvar-node* is a Docker Compose setup that allows to share genomic variants within a secure private group of public nodes. It mainly consists of two Flask applications (**variant-server** and **web-server**) behind a reverse-proxy (**nginx**) that implements two-way SSL encryptation for communication. Variants and their metadata are stored in a MariaDB database (**mariadb**) which is populated by a tool (**data-loader**) that normalizes genomic variants from VCF files (indel left-alignment + biallelification).

*xicvar-node* is intended to run within the private network of an institution, so that the frontend is accessible only to the users of the institution:
- Access to the front-end is controlled by nginx's http basic authentication directive and communication is SSL encrypted.
- Requested variants are normalized and validated on the fly (`bcftools norm --check_ref`) and then forwarded to all configured nodes.
- Ensembl's VEP is used to annotate the effect and consequence of the query variant on genes, transcripts and proteins. The results are displayed on-the-fly in the frontend.
- If requested, the variant liftover will be performed on the fly with Crossmap using the Ensembl chain files.
- Incoming variant requests from external nodes should be routed to port 5000 on the server hosting the Docker setup. Nginx will verify the client's certificate and then redirect the request to the variant server container. Server SSL encryption is achieved using a certificate signed by the network's own CA certificate. Client certificate verification is performed using the nginx ssl_verify_client directive with a certificate also signed by the network's own CA certificate. This setup ensures dedicated two-way SSL encryption between communicating nodes.

![xicvar-node (3)](https://github.com/marcpybus/xicvar-node/assets/12168869/b3c3478c-45c0-45a3-a859-29bde28f2185)

### Installation and configuration
#### Requeriments
- Linux OS (i.e. Ubuntu)
- Docker Compose
- git

#### Installation
```console
git clone https://github.com/marcpybus/xicvar-node.git
cd xicvar-node
docker compose up --build -d
docker compose logs -f
```
### IMPORTANT
The current setup needs to download data to perform normalisation, annotation and liftover of genomic variants.
The first time the web-server container is run, approximately 46 Gb of data will be downloaded:
- Fasta files (GRCh37 and GRCh38 primary assemblies from Ensembl):
  * `https://ftp.ensembl.org/pub/grch37/release-111/fasta/homo_sapiens/dna/Homo_sapiens.GRCh37.dna.primary_assembly.fa.gz`
  * `https://ftp.ensembl.org/pub/release-111/fasta/homo_sapiens/dna/Homo_sapiens.GRCh38.dna.primary_assembly.fa.gz`
- Vep caches (GRCh37 and GRCh38 version 111 VEP caches):
  * `https://ftp.ensembl.org/pub/grch37/release-111/variation/indexed_vep_cache/homo_sapiens_merged_vep_111_GRCh37.tar.gz`
  * `https://ftp.ensembl.org/pub/release-111/variation/indexed_vep_cache/homo_sapiens_merged_vep_111_GRCh38.tar.gz`
- Chain files (GRCh37 to GRCh38 and GRCh38 to GRCh38 liftover files):
  * `https://ftp.ensembl.org/pub/assembly_mapping/homo_sapiens/GRCh37_to_GRCh38.chain.gz`
  * `https://ftp.ensembl.org/pub/assembly_mapping/homo_sapiens/GRCh38_to_GRCh37.chain.gz`

Data downloads can be tracked in Docker logs

### Loading genomic variants from the database
Variants from a VCF files can be loaded into the database using the **data-loader** container:
```console
docker exec -i xicvar-node-data-loader-1 vcf-ingestion.sh grch38 < file.vcf.gz
```
or using docker compose:
```console
cd xicvar-node
docker compose exec -T data-loader vcf-ingestion.sh grch37 < file.vcf
```
- Uncompressed or bgzip-compressed VCF file are allowed and the reference genome version (grch37 or grch38) have to be specified.
- Variants from samples that are already in the databse won't be uploaded. ou should merge all the VCF files from a given sample and reupload them to the database.
- Only variants mapped to primary assembled chromosomes are inserted into the database: 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, X, Y, MT
- Variants with hg19/hg38 chromosome names will be lift over to their equivalent GRCh37/GRCh38 chromosome names.
- Variants will be left-aligned and normalized, and multiallelic sites will be splitted into biallelic records with `bcftools norm --fasta-ref $FASTA --multiallelics -any --check-ref wx`
- Variants containing * (star) or . (missing) alleles won't be included in the database.

### Removing genomic variants from the database
Variants from a given sample can be deleted using the folowing command:
```console
docker exec -i xicvar-node-data-loader-1 remove-sample NA18548 grch38 
```
Or alternatively, you can reset the whole database:
```console
docker exec -i xicvar-node-data-loader-1 remove-db grch37 
```
- In both cases is necessary to specify the reference genome from which the variants will be removed.

### Network configuration
The initial default configuration have dummy certificates configured so the local node (172.18.0.6:5000) can be queried without further configuration. A fake node is also configured for testing purposes.

`networkk-configuration/nodes.json`
```
[
    {"node_name":"DOCKER_IP","node_host":"172.18.0.6:5000"},
    {"node_name":"DOCKER_DOMAIN","node_host":"nginx:5000"},
    {"node_name":"GOOGLE.COM","node_host":"google.com"}
]
```


#### Creating the Certificate Authority's Certificate and Key
```console
openssl req -x509 -newkey rsa:4096 -subj '/CN=Network-Own-CA' -keyout ca-key.pem -out ca-cert.pem -days 36500
```
- use a "very-long" passphrase to encript the key
- certificate expiration is set to 100 years!

#### Creating the Server/Client Key and Certificate Signing Request
```console
openssl req -noenc -newkey rsa:4096 -keyout key.pem -out server-cert.csr
```
#### Signing the Server/Client Certificate Signing Request with the Certificate Authority's Certificate and Key
```console
openssl x509 -req -extfile <(printf "subjectAltName=DNS:<domain.fqdn>,IP:<XXX.XXX.XXX.XXX>") -days 36500 -in server-cert.csr -CA ca-cert.pem -CAkey ca-key.pem -CAcreateserial -out cert.pem
```
- <XXX.XXX.XXX.XXX> use your public IP
- <domain.fqdn> use your domain FQDN 
- certificate expiration is set to 100 years!
