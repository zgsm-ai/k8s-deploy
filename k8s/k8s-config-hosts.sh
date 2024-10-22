#!/bin/sh

#
#   给K8S集群各个节点配置主机名
#

cat /etc/hosts | grep 'k8s hosts' && echo already exists && exit 0

sudo tee -a /etc/hosts <<-'EOF'
# k8s hosts
10.200.101.2 master2
10.200.101.3 master3
10.200.101.4 master4
10.200.101.5 worker1
10.200.101.6 worker2
10.200.101.9 nfs
EOF

