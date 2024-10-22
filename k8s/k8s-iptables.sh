#!/bin/sh

# 相关内核模块
cat > /etc/modules-load.d/ipvs.conf <<EOF
ip_vs
ip_vs_rr
ip_vs_wrr
ip_vs_sh
nf_conntrack
EOF
# 启动服务
systemctl enable --now systemd-modules-load

systemctl stop firewalld
systemctl disable firewalld
