#!/bin/sh

#
#  变更K8s使用的证书，对证书进行重新签名
#
#

cp -r /etc/kubernetes/pki /etc/kubernetes/pki.bak

cat <<EOF > openssl.cnf
[ req ]
default_bits       = 2048
prompt             = no
default_md         = sha256
req_extensions     = req_ext
distinguished_name = dn

[ dn ]
C  = US
ST = California
L  = San Francisco
O  = Kubernetes
OU = System

[ req_ext ]
subjectAltName = @alt_names

[ alt_names ]
DNS.1 = kubernetes
DNS.2 = kubernetes.default
DNS.3 = kubernetes.default.svc
DNS.4 = kubernetes.default.svc.cluster.local
DNS.5 = master.zhuge.sangfor.com
DNS.6 = master2
DNS.7 = master3
DNS.8 = master4
IP.1 = 10.200.101.2
IP.2 = 10.200.101.3
IP.3 = 10.200.101.4
IP.4 = 10.96.0.1
EOF

openssl genpkey -algorithm RSA -out apiserver-key.pem -pkeyopt rsa_keygen_bits:2048
openssl req -new -key apiserver-key.pem -out apiserver.csr -config openssl.cnf

openssl x509 -req -in apiserver.csr -CA /etc/kubernetes/pki/ca.crt -CAkey /etc/kubernetes/pki/ca.key -CAcreateserial -out apiserver.crt -days 3650 -extensions req_ext -extfile openssl.cnf
cp apiserver.crt /etc/kubernetes/pki/apiserver.crt
cp apiserver-key.pem /etc/kubernetes/pki/apiserver.key

systemctl restart kubelet
