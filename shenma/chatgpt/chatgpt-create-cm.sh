#!/bin/sh

kubectl create configmap -n shenma chatgpt-agent-chat-py --from-file=agent_chat.py
kubectl create configmap -n shenma chatgpt-analysis-manager-py --from-file=analysis_manager.py
kubectl create configmap -n shenma chatgpt-apiBot-py --from-file=apiBot.py
kubectl create configmap -n shenma chatgpt-base-es-py --from-file=base_es.py
kubectl create configmap -n shenma chatgpt-configuration-service-py --from-file=configuration_service.py
kubectl create configmap -n shenma chatgpt-events-py --from-file=events.py
kubectl create configmap -n shenma chatgpt-appctx-py --from-file=application_context.py
