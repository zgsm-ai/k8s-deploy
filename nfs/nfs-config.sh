#!/bin/sh

# 安装 NFS 服务器
sudo yum install nfs-utils -y

# 创建共享目录并设置权限
sudo mkdir -p /matrix/data
sudo chown -R nobody:nobody /matrix/data
sudo chmod 777 /matrix/data

# 编辑 /etc/exports 文件
echo "/matrix/data *(rw,sync,no_subtree_check,no_root_squash)" | sudo tee -a /etc/exports

# 启动 NFS 服务
sudo exportfs -rav

sudo systemctl enable nfs-server
sudo systemctl start nfs-server
