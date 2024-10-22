#!/bin/sh

ctr images export cni-v3.25.0.tar quay.io/calico/cni:v3.25.0
ctr images export node-v3.25.0.tar quay.io/calico/node:v3.25.0
ctr images export kube-controllers-v3.25.0.tar quay.io/calico/kube-controllers:v3.25.0

ctr images export kube-apiserver-v1.28.2.tar registry.aliyuncs.com/google_containers/kube-apiserver:v1.28.2
ctr images export kube-controller-manager-v1.28.2.tar registry.aliyuncs.com/google_containers/kube-controller-manager:v1.28.2
ctr images export kube-scheduler-v1.28.2.tar registry.aliyuncs.com/google_containers/kube-scheduler:v1.28.2
ctr images export kube-proxy-v1.28.2.tar registry.aliyuncs.com/google_containers/kube-proxy:v1.28.2
ctr images export pause-3.9.tar registry.aliyuncs.com/google_containers/pause:3.9
ctr images export etcd-3.5.9-0.tar registry.aliyuncs.com/google_containers/etcd:3.5.9-0
ctr images export coredns-v1.10.1.tar registry.aliyuncs.com/google_containers/coredns:v1.10.1
