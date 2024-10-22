#!/bin/sh

echo sh ./yum-config.sh 
echo 重新配置yum,改用阿里源
sh ./yum-config.sh

echo sh ./docker-install.sh 
echo 安装docker-ce
sh ./docker-install.sh

echo sh ./docker-config.sh 
echo 配置docker
sh ./docker-config.sh

echo sh ./k8s-sysctl.sh 
echo 设置K8S需要的sysctl选项
sh ./k8s-sysctl.sh

echo sh ./k8s-swapoff.sh 
echo 关闭swap文件系统
sh ./k8s-swapoff.sh

echo sh ./k8s-iptables.sh 
echo 配置iptables，以及需要的iptables内核模块
sh ./k8s-iptables.sh

echo sh ./k8s-containerd.sh 
echo 配置containerd
sh ./k8s-containerd.sh

echo sh ./k8s-config-repo.sh 
echo 配置K8S的yum源
sh ./k8s-config-repo.sh

echo sh ./k8s-install-software.sh 
echo 安装kubeadm,kubelet,kubectl
sh ./k8s-install-software.sh

echo sh ./k8s-config-hosts.sh 
echo 配置/etc/hosts，把各个节点的hostname加入hosts文件
sh ./k8s-config-hosts.sh

echo sh ./k8s-pull-images.sh
echo 下载必要的镜像
sh ./k8s-pull-images.sh

echo sh ./k8s-init-master.sh 
echo 初始化集群第一个节点，也是master节点
sh ./k8s-init-master.sh

echo sh ./k8s-kubeconfig.sh 
echo 初始化kubeconfig,保证kubectl命令可以管理新产生的k8s集群
sh ./k8s-kubeconfig.sh

echo sh ./k8s-config-calico.sh
echo 使用kubectl命令初始化集群的网络插件，采用calico作为k8s集群网络插件
sh ./k8s-config-calico.sh

