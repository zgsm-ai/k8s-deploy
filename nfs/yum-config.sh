#!/bin/sh

# 删除旧的源
cd /etc/yum.repos.d
mkdir backup
mv *.repo backup/
# 更新为阿里源
wget -O /etc/yum.repos.d/CentOS-Base.repo http://mirrors.aliyun.com/repo/Centos-7.repo
yum clean all
yum makecache
yum update

#为yum操作安装必要的实用工具：
yum install -y yum-utils
