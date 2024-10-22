#!/bin/sh

ctr images export shenma.tar docker.io/apache/apisix-dashboard:3.0.0-alpine \
    docker.io/apache/apisix-ingress-controller:1.8.0 \
    docker.io/apache/apisix:3.9.1-debian \
    docker.io/grafana/grafana:11.2.0 \
    docker.io/nginx:1.27.1 \
    docker.io/postgres:15-alpine \
    quay.io/coreos/etcd:v3.5.5 \
    quay.io/keycloak/keycloak:20.0.2 \
    quay.io/prometheus-operator/prometheus-operator:v0.75.2 \
    quay.io/prometheus/node-exporter:v1.8.2 \
    quay.io/prometheus/prometheus:v2.54.0 \
    quay.io/prometheus/pushgateway:v1.9.0
