# xicvar-node

*xicvar-node* is a Docker Compose setup that allows to share genomic variants within a secure private group of public nodes. It consists of two Flask applications (**variant-server** and **web-server**) that work behind a reverse-proxy (**nginx**) that implements two-way SSL encryptation for communication. Variants and their metadata are stored in a MariaDB database (**mariadb**) which is populated by a software tool (**data-loader**) that normalizes genomic variants from VCF files  (indel left-alignment + biallelification).

*xicvar-node* is intented to be run within an institution's private network so the frontend is only accesible by the institution's users:
- Access to the frontend is controlled using nginx's http basic authentication directive and communication is SSL encrypted.
- Queried variants are normalized and validated on-the-fly by Bcftools (`bcftools norm --check_ref`) and then forwarded to all the configured nodes.
- Ensembl's VEP is used to annotate the effect and consequence of the queried variant on genes, transcripts and proteins. The results are shown on-the-fly in the frontend.
- When requested, variant liftover is performed on-the-fly with Crossmap using Ensembl chain files.
- Incoming variant requests from external nodes should be routed to the port 5000 of the server harboring the project. Nginx will verify the client's certificate and then redirect the request to the variant-server container. Server SSL encryptation is achieved using a certificate signed by the network's own CA certificate. Client certificate verification is performed using nginx ssl_verify_client directive with a certificate also signed by the network's own CA certificate. This setup ensures specific two-way SSL encryptation between communicating nodes.

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
The current setup needs to download data to perform normalization, annotation and liftover of genomic variants
The first time the project is up, it will download arround 46 Gb of data:
- fasta files: GRCh37 and GRCh38 primary assemblies from Ensembl
- vep caches: GRCh37 and GRCh38 version 111 VEP caches
- chain files: GRCh37 to GRCh38 and GRCh38 to GRCh38 liftover files

Data downloading can be tracked in the docker compose logs

### Genomic variants loading
Variants from VCF file can be loaded into the database using the **data-loader** container:
```console
docker exec -i xicvar-node-data-loader-1 vcf-ingestion.sh grch38 < file.vcf.gz
```
or using docker compose:
```console
cd xicvar-node
docker compose exec -T data-loader vcf-ingestion.sh grch37 < file.vcf
```
- You can use an uncompressed or bgzip-compressed VCF file and you have to specify the reference genome version (grch37 or grch38).
- Only variants mapped to primary assembled chromosomes are inserted into the database: 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, X, Y, MT
- Variants with hg19/hg38 chromosome names will be lift over their equivalent GRCh37/GRCh38 chromosome names.
- Variants will be left-aligned and normalized, and multiallelic sites will be splitted into biallelic records, using the following Ensembl primary assemblies and bcftools command line:
 `https://ftp.ensembl.org/pub/grch37/release-111/fasta/homo_sapiens/dna/Homo_sapiens.GRCh37.dna.primary_assembly.fa.gz`
 `https://ftp.ensembl.org/pub/release-111/fasta/homo_sapiens/dna/Homo_sapiens.GRCh38.dna.primary_assembly.fa.gz`
 `bcftools norm --fasta-ref $FASTA --multiallelics -any --check-ref wx`
- Variants containing * (star) or . (missing) alleles won't be included in the database.

### Network configuration
The initial default configuration have dummy certificates configured so the local node (172.18.0.6:5000) can be queried without further configuration.


#### Creating the Certificate Authority's Certificate and Key
```console
openssl req -x509 -newkey rsa:4096 -subj '/CN=My-Own-CA' -keyout ca-key.pem -out ca-cert.pem -days 365
```
- use a "very-long" passphrase to encript the key
- certificate expiration is set to 1 year

#### Creating the Server/Client Key and Certificate Signing Request
```console
openssl req -noenc -newkey rsa:4096 -keyout key.pem -out server-cert.csr
```
#### Signing the Server/Client Certificate Signing Request with the Certificate Authority's Certificate and Key
```console
openssl x509 -req -extfile <(printf "subjectAltName=IP:<XXX.XXX.XXX.XXX>") -days 365 -in server-cert.csr -CA ca-cert.pem -CAkey ca-key.pem -CAcreateserial -out cert.pem
```
- <XXX.XXX.XXX.XXX> use your public IP 
 certificate expiration is set to 1 year
