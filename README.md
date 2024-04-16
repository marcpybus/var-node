# xicvar-node

*xicvar-node* is a Docker Compose setup that allows to share genomic variants within a secure private group of public nodes. It consists of two Flask applications (variant-server and web-server containers) that work behind a reverse-proxy (nginx container) that implements two-way SSL encryptation for communication. Variants and their metadata are stored in a MariaDB database (mariadb container) which is populated by a software tool (data-loader container) that normalizes (indel left-alignment+biallelification) genomic variants from VCF files.

*xicvar-node* is intented to be run within an institution's private network so the frontend is only accesible by the institution's users throught the 443 port. Access to the frontend is controlled using nginx's http basic authentication directive and communication is SSL encrypted. 

Requests to the variant-server are encrypted with a certificate signed by the network's CA certificate. Client is also authenticated with a certificate signed by the network's CA certificate through nginx's "client certificate verification" directive. This implements a server AND client two-way TLS encryptation that secures any communitation between network's nodes.

![xicvar-node (2)](https://github.com/marcpybus/xicvar-node/assets/12168869/d7933ff4-9946-4028-a045-33aed9465fbf)

[ *xicvar-node* has been developed for the Xarxa Interhospitalaria Catalana de Variants Genètiques which was funded by a research grant from "La Marato" in 2019 ]

### Installation



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
