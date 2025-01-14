# var-node-jwt

*var-node-jwt* is a Docker Compose setup that allows to share genomic variants securely across a group of public nodes. It consists of two Flask applications (**variant-server** and **web-server**) behind a reverse-proxy (**nginx**) that implements SSL encryptation for communication. Variant genotypes and associated metadata are stored in a PostgreSQL database (**postgres**), which is populated by a tool (**data-manager**) that automatically normalizes genomic variants from VCF files (indel left-alignment + biallelification).

*var-node* is intended to run within a private network (LAN) of an institution or organization, so that the front end is accessible only to the users from that institution:
- Access to the front end is controlled by nginx's "HTTP Basic Authentication" directive, and communication is SSL encrypted.
- Requested variants are normalized and validated on the fly (`bcftools norm --check_ref`) and then forwarded to all the nodes of the network.
- Ensembl's VEP (`ensembl-vep/vep`) is used to annotate the effect and consequence of the queried variant on genes, transcripts and proteins. Results are also displayed on-the-fly in the front end.
- If requested, variant liftover can be performed on-the-fly with bcftools (`bcftools +liftover`) using Ensembl chain files.
- Incoming variant requests from external nodes have to be routed to port 5000 of the server hosting the Docker setup.
- Server SSL encryption is natively implemented. Authentication is performed using short-lived JWTs.

![var-node-schema-3](https://github.com/user-attachments/assets/6ec463a9-8651-47f6-974c-d8c17f79d774)

### Installation and configuration
#### Requeriments
- Linux OS (i.e. Ubuntu)
- Docker Compose
- git

#### Disk space requirements
- 2GB for Docker images
- 2GB for Fasta and Chain files
- 45GB for Ensembl VEP cache files (optional)

#### Installation
```console
git clone https://github.com/marcpybus/var-node.git
cd var-node
docker compose up --build -d
docker compose logs -f
```
* **ATTENTION:** Approximately 48 GB of genomic data needs to be downloaded and stored in `data/` the first time the **data-manager** container is run. It is possible to reduce disk space requirements by skipping the VEP annotation. See the "Automatic data download" section.
* **IMPORTANT:** Wait until the data has been downloaded and the **data-manager** container has terminated itself. The data download process can be tracked in the container log. 
* To access the front end, use your web browser with the server's IP or domain name. If installed locally, you can use https://localhost/.
* You must configure a username and password before accessing the front end. See the "Configuring the front end password" section.
* Remove the whole `data/` directory to start the data configuration from scratch.

### Setup
- Modify the following variables in `.env` file with the details of your node:
    - Name of the network: `NETWORK_NAME="Network name"`
    - Name of the node: `NODE_NAME="Node name"`
    - Email of contact:`CONTACT_EMAIL="contact@email.com"`
- Add a secure secret key for JWT authetication of incoming requests. **IMPORTANT:** Use this command line `openssl rand -hex 64` to generate a long and secure key:
    - JWT secret key: `JWT_SECRET_KEY="super-secret-key"`
- The default installation comes with a self-signed certificate and key to encrypt all incoming requests. These files are located in `nginx/server-certificates/`. Feel free to modify them and use a properly configured certificate signed by your institution's CA. You should also change the default filenames in the `.env` file:
    - Server certificate: `SERVER_CERT_FILENAME="server.crt"` 
    - Server key: `SERVER_KEY_FILENAME="server.key"`

### Configuring the front end password
To access the front end, you must configure at least one user (and password) using the **data-manager** container:
```console
cd var-node
docker compose run --rm -T data-manager htpasswd -c /data/.htpasswd <username>
```
- `<username>` use your user name
- You will be prompted for a password. Make sure you use a **strong password**!

### Automatic data download
The current setup needs to download data to perform normalisation, annotation and liftover of genomic variants:
- Fasta files (GRCh37 and GRCh38 primary assemblies from Ensembl):
    - `https://ftp.ensembl.org/pub/grch37/release-113/fasta/homo_sapiens/dna/Homo_sapiens.GRCh37.dna.primary_assembly.fa.gz`
    - `https://ftp.ensembl.org/pub/release-113/fasta/homo_sapiens/dna/Homo_sapiens.GRCh38.dna.primary_assembly.fa.gz`
- Chain files (GRCh37 to GRCh38 and GRCh38 to GRCh38 liftover files):
    - `https://ftp.ensembl.org/pub/assembly_mapping/homo_sapiens/GRCh37_to_GRCh38.chain.gz`
    - `https://ftp.ensembl.org/pub/assembly_mapping/homo_sapiens/GRCh38_to_GRCh37.chain.gz`
- Vep caches (GRCh37 and GRCh38 version 113 VEP caches):
    - `https://ftp.ensembl.org/pub/grch37/release-113/variation/indexed_vep_cache/homo_sapiens_merged_vep_113_GRCh37.tar.gz`
    - `https://ftp.ensembl.org/pub/release-113/variation/indexed_vep_cache/homo_sapiens_merged_vep_113_GRCh38.tar.gz`

\* It is possible to skip VEP annotation and reduce disk space requirements. To do so, set the `USE_VEP` variable to `0` in the `.env` file before you run the project. Please note that Fasta files and chain files must be downloaded in order to make actual variant queries.

### Loading genomic variants into the database
Variants from a VCF files can be loaded into the database using the **data-manager** container:
```console
docker compose run --rm -T data-manager vcf-ingestion <grch37|grch38> < file.vcf.gz
```
- Only uncompressed or bgzip-compressed VCF files are allowed, and the reference genome version (grch37 or grch38) must be specified.
- Variants from samples already present in the database won't be uploaded. You should merge all VCF files from a given sample and re-upload them to the database.
- Only variants mapped to primary assembled chromosomes are be added to the database: 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, X, Y, MT
- Variants with hg19/hg38 chromosome names are changed to their corresponding GRCh37/GRCh38 chromosome names.
- Variants are automatically left-aligned and normalised, and multiallelic sites are splitted into biallelic datasets with `bcftools norm --fasta-ref $FASTA --multiallelics -any --check-ref wx`.
- Variants with * (asterisk) or . (missing) alleles won't be included in the database.

#### Load one variant (CUBN:c.4675C>T:p.Pro1559Ser) from 1000genomes samples (GRCh37)
```console
docker compose run --rm -T data-manager vcf-ingestion grch37 < examples/CUBN_c.4675_C_T_p.Pro1559Ser.1kg.vcf.gz
```

#### Load all chromosome 10 variants from all 1000genomes samples (GRCh37)
```console
curl http://ftp.1000genomes.ebi.ac.uk/vol1/ftp/release/20130502/ALL.chr10.phase3_shapeit2_mvncall_integrated_v5b.20130502.genotypes.vcf.gz | docker compose run --rm -T data-manager vcf-ingestion grch37
```
\* please be aware that this upload process may take many hours.

#### Load all chromosome 10 variants from all 1000genomes samples (GRCh38)
```console
curl http://ftp.1000genomes.ebi.ac.uk/vol1/ftp/data_collections/1000_genomes_project/release/20190312_biallelic_SNV_and_INDEL/ALL.chr10.shapeit2_integrated_snvindels_v2a_27022019.GRCh38.phased.vcf.gz | docker compose run --rm -T data-manager vcf-ingestion grch38
```
\* please be aware that this upload process may take many hours.

### Loading sample metadata into the database
Metadata from a TSV files can be loaded into the database using the **data-manager** container:
```console
docker compose run --rm -T data-manager metadata-ingestion <grch37|grch38> < metadata.tsv
```
- Use tab-separated files (TSV). The reference genome version (grch37 or grch38) must be specified.
- The first column must contain the sample name, which must match the sample ID in the VCF file. 
- Subsequent columns in the file will be parsed into a JSON using header names as labels and the resulting JSON will be uploaded to the database.
- Sample genotypes must already exist in the database for the associated metadata to be uploaded.

#### Load metadata from 1000genomes samples (GRCh37)
```console
docker compose run --rm -T data-manager metadata-ingestion grch37 < examples/integrated_call_samples_v3.20130502.ALL.tsv
```
### Removing genomic variants and sample metadata from the database
Variants and metadata from a given sample can be deleted using the folowing command:
```console
docker compose run --rm -T data-manager remove-sample <grch37|grch38> <sample_name>
```
Or alternatively, you can reset the whole database:
```console
docker compose run --rm -T data-manager remove-all-variants <grch37|grch38> 
```
\* In both cases, it is necessary to specify the reference genome from which the variants are to be removed.

### Network node configuration
The default configuration have dummy certificates configured so the nginx container (IP: 172.18.0.6 / Domain: nginx / Port: 5000) can be queried without further configuration. A fake node pointing to google.com is also configured for testing purposes:
```
[
    {"node_name":"This var-node","node_host":"172.18.0.6","node_port":"5000"},
    {"node_name":"GOOGLE.COM","node_host":"google.com","node_port":"443"}
]
```

Modify `network-configuration/nodes.json` to include the domain names or IPs and ports of the nodes you want to connect to.
  
### Credit
@marcpybus
