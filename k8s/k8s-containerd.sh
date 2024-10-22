#!/bin/sh

#
# 安装和配置 containerd
# 需要修改沙盒镜像URL，改用阿里云镜像库中的镜像源
#

cat >>/etc/modules-load.d/containerd.conf <<EOF
overlay
br_netfilter
EOF
# 立刻加载 overlay模块
modprobe overlay
# 立刻加载 br_netfilter模块
modprobe br_netfilter
# 安装containerd
yum install containerd.io -y

mkdir -p /etc/containerd
containerd config default > /etc/containerd/config.toml
# 使用systemd管理cgroups
sed -i '/SystemdCgroup/s/false/true/g' /etc/containerd/config.toml
# 配置sadnbox image从阿里云拉取
sed -i 's#sandbox_image = "registry.k8s.io/pause:3.6"#sandbox_image = "registry.aliyuncs.com/google_containers/pause:3.9"#' /etc/containerd/config.toml
sed -i '/sandbox_image/s/registry.k8s.io/registry.aliyuncs.com\/google_containers/g' /etc/containerd/config.toml
# 启动containerd
systemctl enable containerd
systemctl restart containerd

