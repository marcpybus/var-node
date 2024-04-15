# xicvar-node

*xicvar-node* is a web-based server to share genomic variants within TLS-encrypted private network of nodes. It has been developed for the Xarxa Interhospitalaria Catalana de Variants Genètiques which was funded by a research grant from "La Marato 2019" and it comprises many hospitals in Catalonia.

### Installation

### Installation


### Configure network certificates
#### Creating the Certificate Authority's Certificate and Key
```console
openssl req -x509 -newkey rsa:4096 -subj '/CN=XIC-VAR-CA' -keyout ca-key.pem -out ca-cert.pem -days 365
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
