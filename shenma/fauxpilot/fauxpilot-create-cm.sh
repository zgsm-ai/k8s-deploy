#!/bin/sh

kubectl create configmap -n shenma fauxpilot-common-py --from-file=fauxpilot-common.py
