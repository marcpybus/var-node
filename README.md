# var-node (**beta**)

*var-node* is a Docker Compose setup that allows to share genomic variants securely across a group of public nodes. It consists of two Flask applications (**variant-server** and **web-server**) behind a reverse-proxy (**nginx**) that implements two-way SSL authetication for communication. Variants and their metadata are stored in a MariaDB database (**mariadb**) which is populated by a tool (**data-manager**) that normalizes genomic variants from VCF files (indel left-alignment + biallelification).

*var-node* is intended to run within the private network (LAN) of an institution, so that the frontend is accessible only to the users of the institution:
- Access to the front-end is controlled by nginx's http basic authentication directive and communication is SSL encrypted.
- Requested variants are normalized and validated on the fly (`bcftools norm --check_ref`) and then forwarded to all configured nodes.
- Ensembl's VEP (`ensembl-vep/vep`) is used to annotate the effect and consequence of the queried variant on genes, transcripts and proteins. Results are displayed on-the-fly in the frontend.
- If requested, variant liftover will be performed on the fly with bcftools (`bcftools +liftover`) using the Ensembl chain files.
- Incoming variant requests from external nodes should be routed to port 5000 of the server hosting the Docker setup. SSL encryption is carried out using a certificate signed by the Network’s Own CA Root Certificate. Nginx will verify client's certificate and then redirect the request to the variant-server container. Client certificate verification is performed using the nginx ssl_verify_client directive pointing to the Network’s Own CA Root Certificate. This setup ensures dedicated two-way SSL encryption and authentication between communicating nodes.

![var-node-schema](https://github.com/marcpybus/var-node/assets/12168869/7bbdee09-7fce-45d0-902f-0169924435ac)

### Installation and configuration
#### Requeriments
- Linux OS (i.e. Ubuntu)
- Docker Compose
- git

#### Installation
```console
git clone https://github.com/marcpybus/var-node.git
cd var-node
docker compose up --build -d
docker compose logs -f
```
### Setup
- Modify the folowing variables in `.env` file with the specificities of your node:
    - Internal name of the network: `NETWORK_NAME="Network name"`
    - Internal name of the node: `NODE_NAME="Node name"`
- If your are changing the deafult certificates filenames, please change the folowing variables:
    - CA Root certificate: `CA_CERT_FILENAME="ca-cert.pem"` 
    - Variant-server certificate: `SERVER_CERT_FILENAME="cert.pem"` 
    - Variant-serve key: `SERVER_KEY_FILENAME="key.pem"` 
- The default installation comes with a dummy self-signed certificate and key to encrypt requests from users within the institution. These files are located in `nginx/server-certificates/`. Feel free to change them and use a properly configured certificate signed by your institutions CA. You can also change the default filenames:
    - Front-end certificate: `FRONTEND_CERT_FILENAME="default.crt"` 
    - Front-end key: `FRONTEND_KEY_FILENAME="default.key"` 

### IMPORTANT
The current setup needs to download data to perform normalisation, annotation and liftover of genomic variants.
The first time the web-server container is run, approximately 46 Gb of data will be downloaded and saved in `data/`:
- Fasta files (GRCh37 and GRCh38 primary assemblies from Ensembl):
    - `https://ftp.ensembl.org/pub/grch37/release-111/fasta/homo_sapiens/dna/Homo_sapiens.GRCh37.dna.primary_assembly.fa.gz`
    - `https://ftp.ensembl.org/pub/release-111/fasta/homo_sapiens/dna/Homo_sapiens.GRCh38.dna.primary_assembly.fa.gz`
- Vep caches (GRCh37 and GRCh38 version 111 VEP caches):
    - `https://ftp.ensembl.org/pub/grch37/release-111/variation/indexed_vep_cache/homo_sapiens_merged_vep_111_GRCh37.tar.gz`
    - `https://ftp.ensembl.org/pub/release-111/variation/indexed_vep_cache/homo_sapiens_merged_vep_111_GRCh38.tar.gz`
- Chain files (GRCh37 to GRCh38 and GRCh38 to GRCh38 liftover files):
    - `https://ftp.ensembl.org/pub/assembly_mapping/homo_sapiens/GRCh37_to_GRCh38.chain.gz`
    - `https://ftp.ensembl.org/pub/assembly_mapping/homo_sapiens/GRCh38_to_GRCh37.chain.gz`

\* Data downloading process can be tracked in the docker container logs

### Loading genomic variants from the database
Variants from a VCF files can be loaded into the database using the **data-manager** container:
```console
docker run -i var-node-data-manager-1 vcf-ingestion <grch37|grch38> < file.vcf.gz
```
or using docker compose:
```console
cd var-node
docker compose run -T data-manager vcf-ingestion <grch37|grch38> < file.vcf
```
- Only uncompressed or bgzip-compressed VCF file are allowed, and the reference genome version (grch37 or grch38) have to be specified.
- Variants from samples that are present in the databse won't be uploaded. You should merge all the VCF files from a given sample and reupload them to the database.
- Only variants mapped to primary assembled chromosomes are inserted into the database: 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, X, Y, MT
- Variants with hg19/hg38 chromosome names will be lift over to their equivalent GRCh37/GRCh38 chromosome names.
- Variants will be left-aligned and normalized, and multiallelic sites will be splitted into biallelic records with `bcftools norm --fasta-ref $FASTA --multiallelics -any --check-ref wx`
- Variants containing * (star) or . (missing) alleles won't be included in the database.

#### Load on variant (CUBN:c.4675C>T:p.Pro1559Ser) from 1000genomes VCF
```console
cd var-node
docker compose run -T data-manager vcf-ingestion grch37 < examples/CUBN_c.4675_C_T_p.Pro1559Ser.1kg.vcf.gz
```
\* it can take few hour to upload

#### Load all chromosome 10 variants from 1000genomes VCF
```console
wget https://ftp.1000genomes.ebi.ac.uk/vol1/ftp/release/20130502/ALL.chr10.phase3_shapeit2_mvncall_integrated_v5b.20130502.genotypes.vcf.gz
docker run -i var-node-data-manager-1 vcf-ingestion grch37 < ALL.chr10.phase3_shapeit2_mvncall_integrated_v5b.20130502.genotypes.vcf.gz
```
\* it can take few hour to upload

### Removing genomic variants from the database
Variants from a given sample can be deleted using the folowing command:
```console
docker run -i var-node-data-manager-1 remove-sample <grch37|grch38> <sample_name>
```
Or alternatively, you can reset the whole database:
```console
docker run -i var-node-data-manager-1 remove-all-variants <grch37|grch38> 
```
\* In both cases is necessary to specify the reference genome from which the variants will be removed.

### Network node configuration
The default configuration have dummy certificates configured so the nginx container (IP: 172.18.0.6 / Domain: nginx / Port: 5000) can be queried without further configuration. A fake node pointing to google.com is also configured for testing purposes:
```
[
    {"node_name":"DOCKER_NGINX_IP","node_host":"172.18.0.6","node_port":"5000"},
    {"node_name":"DOCKER_NGINX_DOMAIN","node_host":"nginx","node_port":"5000"},
    {"node_name":"GOOGLE.COM","node_host":"google.com","node_port":"443"}
]
```

Modify `network-configuration/nodes.json` to include the domain names or IPs from the nodes you want to connect with.

### Network certificate configuration
Proper configuration of SSL certificates is essential to make **var-node** a secure way to exchange variant information:
- It is necessary to generate a single CA root certificate and key that will be used to sign all certificates used to encrypt and authenticate communication between nodes. Use a long passphrase for the key.
- The validity of the certificates should be short (i.e. 365 days), forcing the reissuance of new certificates once a year.
- The key and its password should be held by the network administrator, who is responsible for issuing all certificates to valid nodes that provide their Certificate Signing Request file.
- This CA root certificate should be distributed to each configured node along with the signed certificate.

#### Generate the network's CA Root Certificate and Key
```console
docker exec -it var-node-data-manager-server-1 openssl req -x509 -newkey rsa:4096 -subj '/CN=<Network-Own-CA>' -keyout /network-configuration/ca-key.pem -out /network-configuration/ca-cert.pem -days 36500
```
- use a "very-long" passphrase to encript the key
- <Network-Own-CA> use the name of your network of nodes
\* certificate expiration is set to 100 years!

#### Generate server Key and Certificate Signing Request
```console
docker exec -it var-node-data-manager-1 openssl req -noenc -newkey rsa:4096 -keyout /network-configuration/key.pem -out /network-configuration/server-cert.csr
```
#### Sign server Certificate Signing Request with the Certificate Authority's Certificate and Key
```console
docker exec -it var-node-data-manager-1 openssl x509 -req -extfile <(printf "subjectAltName=DNS:<domain.fqdn>,IP:<XXX.XXX.XXX.XXX>") -days 36500 -in /network-configuration/server-cert.csr -CA /network-configuration/ca-cert.pem -CAkey data-managerca-key.pem -CAcreateserial -out /network-configuration/cert.pem
```
- <XXX.XXX.XXX.XXX> use your public IP
- <domain.fqdn> use your domain FQDN 
\* certificate expiration is set to 100 years!

### WAF configuration
Incoming requests have to be redirected to the port 5000 of the server hosting the Docker setup. Two different approaches can be configured with nginx, dependening on the preferences of your institution WAF administrator.

#### SSL Passthrough
As the name suggests, traffic is simply passed through the WAF without being decrypted and towards the port 5000 of the server hosting the Docker setup. This is the easiest configuration as it doesn't requires to reconfigure the WAF by the IT administrator every time the certificates are renewed. This option transfers a higher responsability to the person managing the node, as any putative malicious traffic is also redirected to the node. However it is considered more secure to thrid party manipulations and it doesn't require maintenance from the WAF administrator.

#### SSL Bridging/Offloading
This option requires the WAF to be configured with the network's CA and server certificates to provide SSL encryptation and perform client verification during the process of SSL bridging/offloading. Traffic is then redirected to the port 5000 of the server hosting the Docker setup. Additionally nginx should be configured to only accept requests from the WAF's IP, which would avoid querying the variant-server from within the institution's private network or LAN. As mentioned above, any new issue of certificates would require intervention of the WAF administrator. This configuration could be more easily manipulated by a thrird party (i.e. WAF administrator) and it is considered a less secure option.

### Credit
@marcpybus
