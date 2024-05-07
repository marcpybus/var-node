# var-node (**beta**)

*var-node* is a Docker Compose setup that allows to share genomic variants securely across a group of public nodes. It consists of two Flask applications (**variant-server** and **web-server**) behind a reverse-proxy (**nginx**) that implements client SSL authetication for communication. Variant genotypes and their metadata are stored in a MariaDB database (**mariadb**), which is populated by a tool (**data-manager**) that automatically normalizes genomic variants from VCF files (indel left-alignment + biallelification).

*var-node* is intended to run within a private network (LAN) of an institution or organization, so that the front end is accessible only to the users from that institution:
- Access to the front end is controlled by nginx's "HTTP Basic Authentication" directive, and communication is SSL encrypted.
- Requested variants are normalized and validated on the fly (`bcftools norm --check_ref`) and then forwarded to all the nodes of the network.
- Ensembl's VEP (`ensembl-vep/vep`) is used to annotate the effect and consequence of the queried variant on genes, transcripts and proteins. Results are also displayed on-the-fly in the front end.
- If requested, variant liftover can be performed on-the-fly with bcftools (`bcftools +liftover`) using Ensembl chain files.
- Incoming variant requests from external nodes have to be routed to port 5000 of the server hosting the Docker setup. Server SSL encryption is carried out using a certificate signed by the Network’s Own CA Certificate. Client must also provide a SSL certificate also signed by the Network’s Own CA Certificate. **nginx** can then verify client's certificate and redirect the request to the variant-server container. This setup ensures dedicated two-way SSL encryption and authentication between communicating nodes.

![var-node-schema-2](https://github.com/marcpybus/var-node/assets/12168869/c617ee5e-aff9-4267-901c-c43a721c8bbd)

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
* **ATTENTION:** Approximately 46GB of data needs to be downloaded and stored in `data/` the first time the **data-manager** container is run. It is possible to reduce disk space requirements by skipping the VEP annotation. See the "Data download" section.
* **IMPORTANT:** Wait until the data has been downloaded and the **data-manager** container has terminated itself. The data download process can be tracked in the container log. 
* To access the front end, use your web browser with the server's IP or domain name. If installed locally, you can use https://localhost/.
* You must configure a username and password before accessing the front end. See the "Configuring the front end password" section.
* Remove the whole `data/` directory to start the configuration from scratch.

### Setup
- Modify the following variables in `.env` file with the details of your node:
    - Internal name of the network: `NETWORK_NAME="Network name"`
    - Internal name of the node: `NODE_NAME="Node name"`
- Variant-server certificates are stored in the `network-configuration/` directory. If you change the default certificate filenames, please change the following variables in the `.env` file:
    - CA certificate: `CA_CERT_FILENAME="ca-cert.pem"` 
    - Variant-server certificate: `SERVER_CERT_FILENAME="cert.pem"` 
    - Variant-server key: `SERVER_KEY_FILENAME="key.pem"` 
- The default installation comes with a dummy self-signed certificate and key to encrypt requests from users within the institution. These files are located in `nginx/server-certificates/`. Feel free to modify them and use a properly configured certificate signed by your institution's CA. You should also change the default filenames in the `.env` file:
    - Front-end certificate: `FRONTEND_CERT_FILENAME="default.crt"` 
    - Front-end key: `FRONTEND_KEY_FILENAME="default.key"`

### Configuring the front end password
To access the front end, you must configure at least one user (and password) using the **data-manager** container:
```console
cd var-node
docker compose run -T data-manager htpasswd -c /data/.htpasswd <username>
```
- `<username>` use your user name
- You will be prompted for a password. Make sure you use a **strong password**!

### Data download
The current setup needs to download data to perform normalisation, annotation and liftover of genomic variants:
- Fasta files (GRCh37 and GRCh38 primary assemblies from Ensembl):
    - `https://ftp.ensembl.org/pub/grch37/release-111/fasta/homo_sapiens/dna/Homo_sapiens.GRCh37.dna.primary_assembly.fa.gz`
    - `https://ftp.ensembl.org/pub/release-111/fasta/homo_sapiens/dna/Homo_sapiens.GRCh38.dna.primary_assembly.fa.gz`
- Chain files (GRCh37 to GRCh38 and GRCh38 to GRCh38 liftover files):
    - `https://ftp.ensembl.org/pub/assembly_mapping/homo_sapiens/GRCh37_to_GRCh38.chain.gz`
    - `https://ftp.ensembl.org/pub/assembly_mapping/homo_sapiens/GRCh38_to_GRCh37.chain.gz`
- Vep caches (GRCh37 and GRCh38 version 111 VEP caches):
    - `https://ftp.ensembl.org/pub/grch37/release-111/variation/indexed_vep_cache/homo_sapiens_merged_vep_111_GRCh37.tar.gz`
    - `https://ftp.ensembl.org/pub/release-111/variation/indexed_vep_cache/homo_sapiens_merged_vep_111_GRCh38.tar.gz`

\* It is possible to skip VEP annotation and reduce disk space requirements. To do so, set the `USE_VEP` variable to `0` in the `.env` file before you run the project. Please note that Fasta files and chain files must be downloaded in order to make actual variant queries.

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
- Only uncompressed or bgzip-compressed VCF files are allowed, and the reference genome version (grch37 or grch38) must be specified.
- Variants from samples in the database won't be uploaded. You should merge all VCF files from a given sample and re-upload them to the database.
- Only variants mapped to primary assembled chromosomes are be added to the database: 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, X, Y, MT
- Variants with hg19/hg38 chromosome names are changed to their corresponding GRCh37/GRCh38 chromosome names.
- Variants are left aligned and normalised, and multiallelic sites are splitted into biallelic datasets with `bcftools norm --fasta-ref $FASTA --multiallelics -any --check-ref wx`.
- Variants with * (asterisk) or . (missing) alleles won't be included in the database.

#### Load one variant (CUBN:c.4675C>T:p.Pro1559Ser) from 1000genomes samples
```console
cd var-node
docker compose run -T data-manager vcf-ingestion grch37 < examples/CUBN_c.4675_C_T_p.Pro1559Ser.1kg.vcf.gz
```

#### Load all chromosome 10 variants from 1000genomes samples
```console
wget https://ftp.1000genomes.ebi.ac.uk/vol1/ftp/release/20130502/ALL.chr10.phase3_shapeit2_mvncall_integrated_v5b.20130502.genotypes.vcf.gz
docker run -i var-node-data-manager-1 vcf-ingestion grch37 < ALL.chr10.phase3_shapeit2_mvncall_integrated_v5b.20130502.genotypes.vcf.gz
```
\* please be aware that the upload process may take several hours.

### Removing genomic variants from the database
Variants from a given sample can be deleted using the folowing command:
```console
docker run -i var-node-data-manager-1 remove-sample <grch37|grch38> <sample_name>
```
Or alternatively, you can reset the whole database:
```console
docker run -i var-node-data-manager-1 remove-all-variants <grch37|grch38> 
```
\* In both cases, it is necessary to specify the reference genome from which the variants are to be removed.

### Network node configuration
The default configuration have dummy certificates configured so the nginx container (IP: 172.18.0.6 / Domain: nginx / Port: 5000) can be queried without further configuration. A fake node pointing to google.com is also configured for testing purposes:
```
[
    {"node_name":"DOCKER_NGINX_IP","node_host":"172.18.0.6","node_port":"5000"},
    {"node_name":"DOCKER_NGINX_DOMAIN","node_host":"nginx","node_port":"5000"},
    {"node_name":"GOOGLE.COM","node_host":"google.com","node_port":"443"}
]
```

Modify `network-configuration/nodes.json` to include the domain names or IPs of the nodes you want to connect to. These nodes must present SSL certificates signed by the same CA certificate.

### Network certificates configuration
Proper configuration of SSL certificates is essential to make **var-node** a secure way to exchange variant information:
- It is necessary to generate a single CA certificate and key that have to be used to sign all certificates used to encrypt and authenticate communications between nodes. Use a long passphrase for the key.
- The validity of all certificates should be short (i.e. 365 days), forcing the reissuance of new certificates once a year.
- The key file and its password should be held by the network administrator, who is responsible for issuing all certificates to valid nodes after they have submitted their Certificate Signing Request file.
- This CA certificate should be distributed to each configured node along with the signed certificate.

#### Generate the network's CA certificate and key
```console
docker exec -it var-node-data-manager-server-1 openssl req -x509 -newkey rsa:4096 -subj '/CN=<Network-Own-CA>' -keyout /network-configuration/ca-key.pem -out /network-configuration/ca-cert.pem -days 3650
```
- use a "very-long" passphrase to encript the key
- `<Network-Own-CA>` use the name of your network of nodes
- **ATTENTION:** CA certificate expiration is set to 10 years

#### Generate server key and Certificate Signing Request
```console
docker exec -it var-node-data-manager-1 openssl req -noenc -newkey rsa:4096 -keyout /network-configuration/key.pem -out /network-configuration/server-cert.csr
```
#### Sign server CSR with the CA certificate and Key
```console
docker exec -it var-node-data-manager-1 openssl x509 -req -extfile <(printf "subjectAltName=DNS:<domain.fqdn>,IP:<XXX.XXX.XXX.XXX>") -days 36500 -in /network-configuration/server-cert.csr -CA /network-configuration/ca-cert.pem -CAkey /network-configuration/ca-key.pem -CAcreateserial -out /network-configuration/cert.pem
```
- `<XXX.XXX.XXX.XXX>` use your server public IP
- `<domain.fqdn>` use your server public domain FQDN
- **ATTENTION:** server certificate expiration is set to 365 days

### WAF Configuration
Incoming requests must be redirected to port 5000 on the server hosting the Docker setup. Two different approaches can be configured with nginx, depending on the preferences of your institution's WAF administrator.

#### SSL Passthrough
As the name suggests, traffic is simply passed through the WAF without being decrypted and sent to port 5000 of the server hosting the Docker setup. This is the simplest configuration as it doesn't require the IT administrator to reconfigure the WAF each time the certificates are renewed. This option places more responsibility on the person managing the node, as any hypothetical malicious traffic would also be redirected to the node. However, it is considered more secure against third party manipulation and doesn't require maintenance by the WAF administrator.

#### SSL bridging/offloading
This option requires the WAF to be configured with the network's CA and server certificates to provide SSL encryption and perform client verification during the SSL bridging/offloading process. Traffic is then redirected to port 5000 on the server hosting the Docker setup. In addition, nginx should be configured to only accept requests from the WAF's IP, which would prevent the variant server from being queried from within the institution's private network or LAN. As mentioned above, any reissuance of certificates would require the intervention of the WAF administrator. This configuration could be more easily manipulated by a third party (i.e. WAF administrator) and is considered a less secure option.

### Credit
@marcpybus
