#!/bin/sh

kubeadm join 10.200.101.2:6443 --token ma9yob.pzki8exha98wjdcm \
    --discovery-token-ca-cert-hash sha256:6c0f2c33ea84884a1850bd8a2ee3bad2a5c763ad69b1da9b29cabc7a77c3dea1 
