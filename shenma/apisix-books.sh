#!/bin/sh

AUTH="X-API-KEY: edd1c9f034335f136f87ad84b625c8f1" 
TYPE="Content-Type: application/json"
APISIX_ADDR="10.200.101.5:30180"
KEYCLOAK_ADDR="http://zgsm.sangfor.com"
SHENMA_ADDR="https://zgsm.sangfor.com"

curl -i http://$APISIX_ADDR/apisix/admin/upstreams -H "$AUTH" -H "$TYPE" -X PUT  -d '{
    "id": "books",
    "nodes": {
        "books.shenma.svc.cluster.local:8080": 1
    },
    "type": "roundrobin"
}'

curl -i  http://$APISIX_ADDR/apisix/admin/routes -H "$AUTH" -H "$TYPE" -X PUT -d '{
    "uri": "/books/*",
    "id": "books",
    "upstream_id": "books",
    "plugins": {
      "openid-connect": {
        "client_id": "apisix",
        "client_secret": "IKUMXXsVLgdU59nk6kXFuiqYEuB0D3Xw",
        "discovery": "'"$KEYCLOAK_ADDR"'/realms/gw/.well-known/openid-configuration",
        "introspection_endpoint_auth_method": "client_secret_basic",
        "realm": "gw",
        "bearer_only": false,
        "redirect_uri": "'"$SHENMA_ADDR"'/books/",
        "logout_path": "/books/logout",
        "redirect_login": false
      }
    }
  }'
