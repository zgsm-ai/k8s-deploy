#!/bin/sh

cp *.jar /mnt/nfs/shenma-keycloak-providers-pvc-80f25ddd-94f5-4add-8bc4-d75db6ec0051/
kubectl delete deployment -n shenma keycloak
kubectl apply -f keycloak-build.yaml
kubectl apply -f keycloak.yaml
kubectl describe deployment -n shenma keycloak
