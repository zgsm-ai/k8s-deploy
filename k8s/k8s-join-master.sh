#!/bin/sh

kubeadm join 10.200.101.2:6443 --token x0qnmb.veqdkm1kiwe60joa --discovery-token-ca-cert-hash sha256:6c0f2c33ea84884a1850bd8a2ee3bad2a5c763ad69b1da9b29cabc7a77c3dea1 --control-plane --certificate-key af544c2c3434d1c86b0474f6f8de80fb3b2776f66bc8905ed46eb914e37e3718
