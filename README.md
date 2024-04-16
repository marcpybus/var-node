# xicvar-node

*xicvar-node* is a Docker Compose setup that allows to share genomic variants within a secure private group of public nodes. It consists of two Flask applications (variant-server and web-server containers) that work behind a reverse-proxy (nginx container) that implements two-way SSL encryptation for communication. Variants and their metadata are stored in a MariaDB database (mariadb container) which is populated by a software tool (data-loader container) that normalizes (indel left-alignment + biallelification) genomic variants from VCF files.

*xicvar-node* is intented to be run within an institution's private network so the frontend is only accesible by the institution's users:
- Access to the frontend is controlled using nginx's http basic authentication directive and communication is SSL encrypted.
- Queried variants are normalized and validated on-the-fly by Bcftools (```bcftools norm --check_ref```) and then forwarded to all the configured nodes.
- Ensembl VEP is used to annotate the queried variant and its results are showed in the frontend.
- Liftover is also performed on-the-fly with Crossmap using Ensembl chain files when requested.
- Incoming variant requests from external nodes are routed to the port 5000 in the nginx container, client verified and then redirected to the variant-server container. Typical SSL encryptation is carried out using certificates signed by the network's own CA certificate. Client verification is also performed using nginx ssl_verify_client directive with certificates also signed by the network's own CA certificate. This setup ensures specific two-way SSL encryptation between communicating nodes.

![xicvar-node (3)](https://github.com/marcpybus/xicvar-node/assets/12168869/b3c3478c-45c0-45a3-a859-29bde28f2185)

### Installation and configuration
#### Requeriments
- Linux OS
- Docker Compose

#### Installation
```console
git clone https://github.com/marcpybus/xicvar-node.git
```
### Configuration



### Configure network certificates
#### Creating the Certificate Authority's Certificate and Key
```console
openssl req -x509 -newkey rsa:4096 -subj '/CN=My-Own-CA' -keyout ca-key.pem -out ca-cert.pem -days 365
```
* use a "very-long" passphrase to encript the key
* certificate expiration is set to 1 year

#### Creating the Server/Client Key and Certificate Signing Request
```console
openssl req -noenc -newkey rsa:4096 -keyout key.pem -out server-cert.csr
```
#### Signing the Server/Client Certificate Signing Request with the Certificate Authority's Certificate and Key
```console
openssl x509 -req -extfile <(printf "subjectAltName=IP:<XXX.XXX.XXX.XXX>") -days 365 -in server-cert.csr -CA ca-cert.pem -CAkey ca-key.pem -CAcreateserial -out cert.pem
```
* <XXX.XXX.XXX.XXX> use the server's IP 
* certificate expiration is set to 1 year
