#!/bin/sh

AUTH="X-API-KEY: edd1c9f034335f136f87ad84b625c8f1" 
TYPE="Content-Type: application/json"
APISIX_ADDR="172.16.0.2:9180"
KEYCLOAK_ADDR="http://172.16.0.2:8080"
SHENMA_ADDR="https://zgsm.sangfor.com"

curl -i http://$APISIX_ADDR/apisix/admin/upstreams -H "$AUTH" -H "$TYPE" -X PUT  -d '{
    "id": "portal",
    "nodes": {
        "172.16.0.2:9081": 1
    },
    "type": "roundrobin"
}'

curl -i  http://$APISIX_ADDR/apisix/admin/routes -H "$AUTH" -H "$TYPE" -X PUT -d '{
    "uri": "/portal/*",
    "id": "portal",
    "upstream_id": "portal",
    "plugins": {
      "openid-connect": {
        "client_id": "apisix",
        "client_secret": "IKUMXXsVLgdU59nk6kXFuiqYEuB0D3Xw",
        "discovery": "'"$KEYCLOAK_ADDR"'/realms/gw/.well-known/openid-configuration",
        "introspection_endpoint_auth_method": "client_secret_basic",
        "realm": "gw",
        "bearer_only": false,
        "redirect_uri": "'"$SHENMA_ADDR"'/portal/",
        "logout_path": "/portal/logout",
        "redirect_login": false
      }
    }
  }'
