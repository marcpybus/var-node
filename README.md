# Xarxa Interhospitalaria Catalana de Variants Genètiques
## Node software documentation



### Installation


### Configure network certificates
#### Creating the Certificate Authority's Certificate and Key
```console
openssl req -x509 -newkey rsa:4096 -subj '/CN=XIC-VAR-CA' -keyout ca-key.pem -out ca-cert.pem -days 3650
```
* please use a "very-long" passphrase to encript the key
* certificate expiration is set to 1 year

#### Creating the Server/Client Key and Certificate Signing Request
```console
openssl req -noenc -newkey rsa:4096 -keyout key.pem -out server-cert.csr
```
#### Signing the Server/Client Certificate Signing Request with the Certificate Authority's Certificate and Key
```console
openssl x509 -req -extfile <(printf "subjectAltName=IP:<XXX.XXX.XXX.XXX>") -days 3650 -in server-cert.csr -CA ca-cert.pem -CAkey ca-key.pem -CAcreateserial -out cert.pem
```
* <XXX.XXX.XXX.XXX> use the server's IP 
* certificate expiration is set to 1 year