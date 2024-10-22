#!/bin/sh

ctr images import cni-v3.25.0.tar 
ctr images import node-v3.25.0.tar
ctr images import kube-controllers-v3.25.0.tar 

ctr images import kube-apiserver-v1.28.2.tar 
ctr images import kube-controller-manager-v1.28.2.tar 
ctr images import kube-scheduler-v1.28.2.tar 
ctr images import kube-proxy-v1.28.2.tar 
ctr images import pause-3.9.tar 
ctr images import etcd-3.5.9-0.tar 
ctr images import coredns-v1.10.1.tar 
