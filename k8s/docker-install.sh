#!/bin/sh

#
#   使用阿里云的docker-ce软件源安装docker-ce
#

yum-config-manager --add-repo http://mirrors.aliyun.com/docker-ce/linux/centos/docker-ce.repo
yum -y install docker-ce

systemctl enable docker
systemctl start docker
