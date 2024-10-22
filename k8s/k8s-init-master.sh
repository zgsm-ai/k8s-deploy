#!/bin/sh

kubeadm init --kubernetes-version=1.28.2                        \
    --apiserver-advertise-address=10.200.101.2                  \
    --image-repository  registry.aliyuncs.com/google_containers \
    --pod-network-cidr=10.244.0.0/16

#--control-plane-endpoint "master.zhuge.sangfor.com:6443" 
