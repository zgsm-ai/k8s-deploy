#!/bin/sh

docker pull registry.aliyuncs.com/google_containers/kube-apiserver:v1.28.2
docker pull registry.aliyuncs.com/google_containers/kube-controller-manager:v1.28.2
docker pull registry.aliyuncs.com/google_containers/kube-scheduler:v1.28.2
docker pull registry.aliyuncs.com/google_containers/kube-proxy:v1.28.2
docker pull registry.aliyuncs.com/google_containers/pause:3.9
docker pull registry.aliyuncs.com/google_containers/etcd:3.5.9-0
docker pull registry.aliyuncs.com/google_containers/coredns:v1.10.1
docker pull quay.io/calico/cni:v3.25.0
docker pull quay.io/calico/node:v3.25.0
docker pull quay.io/calico/kube-controllers:v3.25.0

ctr images pull registry.aliyuncs.com/google_containers/kube-apiserver:v1.28.2
ctr images pull registry.aliyuncs.com/google_containers/kube-controller-manager:v1.28.2
ctr images pull registry.aliyuncs.com/google_containers/kube-scheduler:v1.28.2
ctr images pull registry.aliyuncs.com/google_containers/kube-proxy:v1.28.2
ctr images pull registry.aliyuncs.com/google_containers/pause:3.9
ctr images pull registry.aliyuncs.com/google_containers/etcd:3.5.9-0
ctr images pull registry.aliyuncs.com/google_containers/coredns:v1.10.1

ctr images pull quay.io/calico/cni:v3.25.0
ctr images pull quay.io/calico/node:v3.25.0
ctr images pull quay.io/calico/kube-controllers:v3.25.0
