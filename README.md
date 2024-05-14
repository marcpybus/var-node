# var-node (**beta**)

*var-node* is a Docker Compose setup that allows to share genomic variants securely across a group of public nodes. It consists of two Flask applications (**variant-server** and **web-server**) behind a reverse-proxy (**nginx**) that implements client SSL authentication for communication. Variant genotypes and their metadata are stored in a MariaDB database (**mariadb**), which is populated by a tool (**data-manager**) that automatically normalizes genomic variants from VCF files (indel left-alignment + biallelification).

*var-node* is intended to run within a private network (LAN) of an institution or organization, so that the front end is accessible only to the users from that institution:
- Access to the front end is controlled by nginx's "HTTP Basic Authentication" directive, and communication is SSL encrypted.
- Requested variants are normalized and validated on the fly (`bcftools norm --check_ref`) and then forwarded to all the nodes of the network.
- Ensembl's VEP (`ensembl-vep/vep`) is used to annotate the effect and consequence of the queried variant on genes, transcripts and proteins. Results are also displayed on-the-fly in the front end.
- If requested, variant liftover can be performed on-the-fly with bcftools (`bcftools +liftover`) using Ensembl chain files.
- Incoming variant requests from external nodes have to be routed to port 5000 of the server hosting the Docker setup. Server SSL encryption is natively implemented. Client must provide a SSL certificate signed by the Network’s Own CA Certificate with a CN (Common Name) matching client's public IP. Request is then authenticated and redirected to the variant-server container. This setup ensures SSL encryption and authentication for all incoming requests.

![var-node-schema-2](https://github.com/marcpybus/var-node/assets/12168869/c617ee5e-aff9-4267-901c-c43a721c8bbd)

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
* **ATTENTION:** Approximately 48 GB of genomic data needs to be downloaded and stored in `data/` the first time the **data-manager** container is run. It is possible to reduce disk space requirements by skipping the VEP annotation. See the "Data download" section.
* **IMPORTANT:** Wait until the data has been downloaded and the **data-manager** container has terminated itself. The data download process can be tracked in the container log. 
* To access the front end, use your web browser with the server's IP or domain name. If installed locally, you can use https://localhost/.
* You must configure a username and password before accessing the front end. See the "Configuring the front end password" section.
* Remove the whole `data/` directory to start the data configuration from scratch.

### Setup
- Modify the following variables in `.env` file with the details of your node:
    - Internal name of the network: `NETWORK_NAME="Network name"`
    - Internal name of the node: `NODE_NAME="Node name"`
- Client certificates are stored in the `network-configuration/` directory. If you change the default certificate filenames, please change the following variables in the `.env` file:
    - CA certificate: `CA_CERT_FILENAME="ca-cert.pem"` 
    - Client certificate: `CLIENT_CERT_FILENAME="client-cert.pem"` 
    - Client key: `CLIENT_KEY_FILENAME="client-key.pem"` 
- The default installation comes with a self-signed certificate and key to encrypt all incoming requests. These files are located in `nginx/server-certificates/`. Feel free to modify them and use a properly configured certificate signed by your institution's CA. You should also change the default filenames in the `.env` file:
    - Server certificate: `SERVER_CERT_FILENAME="server.crt"` 
    - Server key: `SERVER_KEY_FILENAME="server.key"`

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
docker compose run -T data-manager vcf-ingestion <grch37|grch38> < file.vcf.gz
```
- Only uncompressed or bgzip-compressed VCF files are allowed, and the reference genome version (grch37 or grch38) must be specified.
- Variants from samples in the database won't be uploaded. You should merge all VCF files from a given sample and re-upload them to the database.
- Only variants mapped to primary assembled chromosomes are be added to the database: 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, X, Y, MT
- Variants with hg19/hg38 chromosome names are changed to their corresponding GRCh37/GRCh38 chromosome names.
- Variants are left aligned and normalised, and multiallelic sites are splitted into biallelic datasets with `bcftools norm --fasta-ref $FASTA --multiallelics -any --check-ref wx`.
- Variants with * (asterisk) or . (missing) alleles won't be included in the database.

#### Load one variant (CUBN:c.4675C>T:p.Pro1559Ser) from 1000genomes samples
```console
docker compose run -T data-manager vcf-ingestion grch37 < examples/CUBN_c.4675_C_T_p.Pro1559Ser.1kg.vcf.gz
```

#### Load all chromosome 10 variants from 1000genomes samples
```console
curl http://ftp.1000genomes.ebi.ac.uk/vol1/ftp/release/20130502/ALL.chr10.phase3_shapeit2_mvncall_integrated_v5b.20130502.genotypes.vcf.gz | docker compose run -T data-manager vcf-ingestion grch37
```
\* please be aware that the upload process may take several hours.

### Removing genomic variants from the database
Variants from a given sample can be deleted using the folowing command:
```console
docker compose run -T data-manager remove-sample <grch37|grch38> <sample_name>
```
Or alternatively, you can reset the whole database:
```console
docker compose run -T data-manager remove-all-variants <grch37|grch38> 
```
\* In both cases, it is necessary to specify the reference genome from which the variants are to be removed.

### Network node configuration
The default configuration have dummy certificates configured so the nginx container (IP: 172.18.0.6 / Domain: nginx / Port: 5000) can be queried without further configuration. A fake node pointing to google.com is also configured for testing purposes:
```
[
    {"node_name":"DOCKER_NGINX_IP","node_host":"172.18.0.6","node_port":"5000"},
    {"node_name":"GOOGLE.COM","node_host":"google.com","node_port":"443"}
]
```

Modify `network-configuration/nodes.json` to include the domain names or IPs and ports of the nodes you want to connect to.

### Network certificates configuration
Proper configuration of SSL client certificates is essential to make **var-node** a secure way to exchange variant information:
- It is necessary to generate a single CA certificate and key for the whole network of nodes that have to be used to sign all certificates used to authenticate client requests. Remember to use a **very long** passphrase for the key.
- The validity of all client certificates should be short (i.e. 365 days), forcing the reissuance of new certificates regularly.
- The key file and its password should be held by the network administrator, who is responsible for issuing all client certificates to valid nodes after they have submitted their Certificate Signing Request file.
- The CA certificate should be distributed to each configured node along with the signed client certificate.

#### Generate the network's CA certificate and key
```console
docker compose run -T data-manager openssl req -x509 -newkey rsa:4096 -subj '/CN=<Network-Name>' -keyout /network-configuration/ca-key.pem -out /network-configuration/ca-cert.pem -days 3650
```
- use a **very long** passphrase to encript the key
- `<Network-Name>` use the name of your network of nodes
- **ATTENTION:** CA certificate expiration is set to 10 years

#### Generate client key and Certificate Signing Request
```console
docker compose run -T data-manager openssl req -noenc -newkey rsa:4096 -subj '/CN=<XXX.XXX.XXX.XXX>' -keyout /network-configuration/client-key.pem -out /network-configuration/client-cert.csr
```
- `<XXX.XXX.XXX.XXX>` use your public IP

#### Sign client CSR with the CA certificate and key
```console
docker compose run -T data-manager openssl x509 -req -days 365 -in /network-configuration/client-cert.csr -CA /network-configuration/ca-cert.pem -CAkey /network-configuration/ca-key.pem -CAcreateserial -out /network-configuration/client-cert.pem
```
- **ATTENTION:** client certificate expiration is set to 365 days

### WAF Configuration
Incoming requests must be redirected to port 5000 of the server hosting the Docker setup. Two different approaches can be configured with nginx, depending on the preferences of your institution's WAF administrator.

#### SSL Passthrough
As the name suggests, all traffic is simply passed through the WAF without being decrypted (SSL offloading) and sent to port 5000 of the server hosting the Docker setup. This is the simplest configuration as it doesn't require further WAF configuration. This option places more responsibility on the person managing the node, as any hypothetical malicious traffic would also be redirected to the node. However, it is considered more secure against third party manipulation.

- This is the current default configuration. Variable `CLIENT_VERIFICATION` must be set to `"var-node"` in the `.env` file. 
- Beware that **nginx** will automatically match certificate's CN to client request IP to fully authenticate valid requests from valid IPs!

#### SSL bridging/offloading
This option requires the WAF to be configured with the network's CA certificate to perform client verification during the SSL bridging/offloading process. Traffic is then redirected to port 5000 on the server hosting the Docker setup. In addition, nginx should be configured to only accept requests from the WAF's IP, which would prevent the variant server from being queried from within the institution's private network or LAN. Any reissuance a new CA certificate would require the intervention of the WAF administrator. This configuration could be more easily manipulated by a third party (i.e. WAF administrator) and is considered a less secure option.

- This configuration requires the `CLIENT_VERIFICATION` variable in the `.env` file to be set to `"waf"`. In addition, the `WAF_IP` variable should contain the IP of the WAF.
- Be sure that SSL client authetication is correctly performed by WAF. All requests coming from WAF's IP will be considered as valid requests. use this configuration at your risk.
  
### Credit
@marcpybus
