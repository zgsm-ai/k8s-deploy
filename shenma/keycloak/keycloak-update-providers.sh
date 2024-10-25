#!/bin/sh

# 先备份原有jar
BACKUP=`date +"%Y%m%d-%H%M"`
mkdir -p ./backups/$BACKUP
cp /mnt/nfs/shenma-keycloak-providers-pvc-80f25ddd-94f5-4add-8bc4-d75db6ec0051/*.jar ./backups/$BACKUP/ 

# 拷贝新的jar到keycloak的/opt/keycloak/providers目录
cp *.jar /mnt/nfs/shenma-keycloak-providers-pvc-80f25ddd-94f5-4add-8bc4-d75db6ec0051/

# 先停掉keycloak
kubectl delete deployment -n shenma keycloak
# 执行kc.sh build命令
kubectl apply -f keycloak-build.yaml
# 重新启动keycloak
kubectl apply -f keycloak.yaml
kubectl describe deployment -n shenma keycloak
