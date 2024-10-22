#!/bin/sh

AUTH="X-API-KEY: edd1c9f034335f136f87ad84b625c8f1" 
TYPE="Content-Type: application/json"
APISIX_ADDR="10.200.101.5:30180"
KEYCLOAK_ADDR="http://zgsm.sangfor.com"

curl -i http://$APISIX_ADDR/apisix/admin/upstreams -H "$AUTH" -H "$TYPE" -X PUT  -d '{
    "id": "chatgpt",
    "nodes": {
      "chatgpt.shenma.svc.cluster.local:5000": 1
    },
    "type": "roundrobin"
  }'

curl -i http://$APISIX_ADDR/apisix/admin/upstreams -H "$AUTH" -H "$TYPE" -X PUT  -d '{
    "id": "websocket",
    "nodes": {
      "chatgpt.shenma.svc.cluster.local:8765": 1
    },
    "type": "roundrobin"
  }'

curl -i  http://$APISIX_ADDR/apisix/admin/routes -H "$AUTH" -H "$TYPE" -X PUT -d '{
    "uris": ["/chat/*", "/api/*", "/answer", "/answer/*"],
    "id": "chatgpt",
    "upstream_id": "chatgpt",
    "plugins": {
      "limit-req": {
        "rate": 1,
        "burst": 1,
        "rejected_code": 503,
        "key_type": "var",
        "key": "remote_addr"
      },
      "limit-count": {
        "count": 100,
        "time_window": 86400,
        "rejected_code": 429,
        "key": "remote_addr"
      },
      "file-logger": {
        "path": "logs/access.log",
        "include_req_body": true,
        "include_resp_body": true
      }
    }
  }'

curl -i  http://$APISIX_ADDR/apisix/admin/routes -H "$AUTH" -H "$TYPE" -X PUT -d '{
    "uris": ["/socket.io/*"],
    "id": "websocket",
    "upstream_id": "websocket",
    "enable_websocket": true,
    "plugins": {
      "file-logger": {
        "path": "logs/access.log",
        "include_req_body": true,
        "include_resp_body": true
      }
    }
  }'

      # "proxy-rewrite": {
      #   "regex_uri": ["^/socket.io/(.*)", "/$1"]
      # },
# curl -i  http://$APISIX_ADDR/apisix/admin/routes -H "$AUTH" -H "$TYPE" -X PUT -d '{
#     "uris": ["/socket.io", "/socket.io/*", "chat/*", "/api/*", "/answer", "/answer/*"],
#     "id": "chatgpt",
#     "upstream_id": "chatgpt",
#     "plugins": {
#       "openid-connect": {
#         "client_id": "vscode",
#         "client_secret": "jFWyVy9wUKKSkX55TDBt2SuQWl7fDM1l",
#         "discovery": "'"$KEYCLOAK_ADDR"'/realms/gw/.well-known/openid-configuration",
#         "introspection_endpoint_auth_method": "client_secret_basic",
#         "realm": "gw",
#         "bearer_only": true,
#         "ssl_verify": false
#       },
#       "limit-req": {
#         "rate": 1,
#         "burst": 2,
#         "rejected_code": 503,
#         "key_type": "var",
#         "key": "remote_addr"
#       },
#       "limit-count": {
#         "count": 100,
#         "time_window": 86400,
#         "rejected_code": 429,
#         "key": "remote_addr"
#       },
#       "file-logger": {
#         "path": "logs/access.log",
#         "include_req_body": true,
#         "include_resp_body": true
#       }
#     }
#   }'

# curl -i  http://$APISIX_ADDR/apisix/admin/routes -H "$AUTH" -H "$TYPE" -X PUT -d '{
#     "uris": ["/v1/completions", "/v2/completions", "/chatgpt_internal/*", "/v2/engines/*", "/v1/engines/*"],
#     "id": "chatgpt",
#     "upstream_id": "chatgpt",
#     "plugins": {
#       "file-logger": {
#         "path": "logs/access.log",
#         "include_req_body": true,
#         "include_resp_body": true
#       }
#     }
#   }'
