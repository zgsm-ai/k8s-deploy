#!/bin/sh

#
# 配置calico为k8s的网络插件，
# calico.yaml内容来自https://docs.projectcalico.org/manifests/calico.yaml
# 需要进行如下修改：
# 1. 修改IP自动发现所依赖的网卡名，IP_AUTODETECTION_METHOD: "interface=eth0"
# 2. 修改IP池地址范围：CALICO_IPV4POOL_CIDR: "10.244.0.0/16"
#

kubectl apply -f calico.yaml
