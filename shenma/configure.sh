#!/bin/sh

AUTH="X-API-KEY: b28817646142cc3df7ecf1acfed50e48" 
TYPE="Content-Type: application/json"
APISIX_ADDR="10.200.101.5:30180"

KEYCLOAK_ADDR="http://10.200.101.5:30880"
KEYCLOAK_CLIENT_ID="vscode"
KEYCLOAK_CLIENT_SECRET="jFWyVy9wUKKSkX55TDBt2SuQWl7fDM1l"
KEYCLOAK_REALM="gw"
KEYCLOAK_UI_DOMAIN="iodim"

OPENAI_MODEL_HOST="http://172.16.254.5:32081/v1/completions"
OPENAI_MODEL="DeepSeek-Coder-V2-Lite-Base"

ONE_API_INITIAL_ROOT_KEY="966c3157fe65461dbc731cd540b6cd5d"
ONE_API_AWS_PROXY="http://13.71.87.0:32088"
ONE_API_FAKE_OPENAI="10.200.101.5"
ONE_API_FAKE_ANTHROPIC="10.200.101.9"

PGSQL_ADDR="postgres.shenma.svc.cluster.local:5432"
REDIS_ADDR="redis.shenma.svc.cluster.local:6379"
AIGW_HOST="higress.shenma.svc.cluster.local"
AIGW_PORT="8080"
AIGW_CHAT_ADDR="http://higress.shenma.svc.cluster.local:8080/v1/chat/completions"
AIGW_COMPLETION_ADDR="http://172.16.254.5:32081/v1/completions"

NAMESPACE="shenma"
OIDC_CLIENT_ID="7c51a6b92dfebfa55d96"
OIDC_CLIENT_SECRET="bcb3dc222a07fad21aabdd5035dadba2f09e05d6"
OIDC_HOST="casdoor.shenma.svc.cluster.local"
OIDC_PORT="8000"
OIDC_DISCOVERY_ADDR="http://casdoor.shenma.svc.cluster.local:8000/.well-known/openid-configuration"
OIDC_INTROSPECTION_ENDPOINT="http://casdoor.shenma.svc.cluster.local:8000/api/login/oauth/introspect"