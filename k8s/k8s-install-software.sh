#!/bin/sh

yum install -y kubeadm kubelet kubectl

systemctl enable kubelet
systemctl start kubelet
