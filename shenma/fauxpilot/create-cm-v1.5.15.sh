#!/bin/sh

kubectl create configmap -n shenma fauxpilot-common-py --from-file=common-v1.5.15.py
