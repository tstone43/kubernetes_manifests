# 1. Generate key and SAN config
openssl genrsa -out dashboard.key 2048

cat > dashboard.conf << EOF
[req]
distinguished_name = req_distinguished_name
req_extensions = v3_req
prompt = no

[req_distinguished_name]
O = IT
CN = ceph-dashboard

[v3_req]
keyUsage = keyEncipherment, dataEncipherment
extendedKeyUsage = serverAuth
subjectAltName = @alt_names

[alt_names]
DNS.1 = rook-ceph-mgr-dashboard.rook-ceph.svc.cluster.local
DNS.2 = rook-ceph-mgr-dashboard
IP.1 = 10.43.82.141
EOF

# 2. Generate self-signed cert with SANs
openssl req -new -x509 -days 365 -key dashboard.key -out dashboard.crt \
  -config dashboard.conf -extensions v3_req

# Copy cert
cat dashboard.crt | kubectl exec -i -n rook-ceph deploy/rook-ceph-tools -- cat > /tmp/dashboard.crt

# Copy key  
cat dashboard.key | kubectl exec -i -n rook-ceph deploy/rook-ceph-tools -- cat > /tmp/dashboard.key

ceph dashboard set-ssl-certificate -i /tmp/dashboard.crt
ceph dashboard set-ssl-certificate-key -i /tmp/dashboard.key
ceph mgr fail $(ceph mgr dump | jq -r .active_name)