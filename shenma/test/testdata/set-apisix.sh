#!/bin/sh

AUTH="X-API-KEY: edd1c9f034335f136f87ad84b625c8f1" 
TYPE="Content-Type: application/json"
APISIX_ADDR="10.200.101.5:30180"
KEYCLOAK_ADDR="10.200.101.5:30880"
SHENMA_ADDR="10.200.101.5:30080"
SHENMA_IP="10.200.101.5"

curl -i http://$APISIX_ADDR/apisix/admin/upstreams -H "$AUTH" -H "$TYPE" -X PUT  -d '{
    "id": "web1",
    "nodes": {
        "web1.shenma.svc.cluster.local:9081": 1
    },
    "type": "roundrobin"
}'

curl -i http://$APISIX_ADDR/apisix/admin/upstreams -H "$AUTH" -H "$TYPE" -X PUT -d '{
    "id": "web2",
    "nodes": {
        "web2.shenma.svc.cluster.local:9082": 1
    },
    "type": "roundrobin"
}'

curl -i http://$APISIX_ADDR/apisix/admin/upstreams -H "$AUTH" -H "$TYPE" -X PUT -d '{
    "id": "shenma",
    "nodes": {
        "web2.shenma.svc.cluster.local:9082": 1
    },
    "type": "roundrobin"
}'

curl -i http://$APISIX_ADDR/apisix/admin/routes -H "$AUTH" -H "$TYPE" -X PUT -d '{
    "id": "web1",
    "uri": "/web1/*",
    "upstream_id": "web1",
    "plugins": {
        "openid-connect": {
            "client_id": "apisix",
            "client_secret": "g5cxUb10HB1D0V1ErgVwssKsqg6rWLPj",
            "discovery": "http://'"$KEYCLOAK_ADDR"'/realms/gw/.well-known/openid-configuration",
            "introspection_endpoint_auth_method": "client_secret_basic",
            "bearer_only": false,
            "realm": "gw"
        }
    }
}'

curl -i http://$APISIX_ADDR/apisix/admin/routes -H "$AUTH" -H "$TYPE" -X PUT -d '{
    "id": "web2",
    "uri": "/web2/*",
    "upstream_id": "web2",
    "plugins": {
        "openid-connect": {
            "client_id": "apisix",
            "client_secret": "g5cxUb10HB1D0V1ErgVwssKsqg6rWLPj",
            "discovery": "http://'"$KEYCLOAK_ADDR"'/realms/gw/.well-known/openid-configuration",
            "introspection_endpoint_auth_method": "client_secret_basic",
            "bearer_only": false,
            "realm": "gw"
        }
    }
}'

curl -i  http://$APISIX_ADDR/apisix/admin/routes -H "$AUTH" -H "$TYPE" -X PUT -d '{
    "uri": "/project-manage/*",
    "id": "pm1",
    "plugins": {
      "openid-connect": {
        "client_id": "apisix",
        "client_secret": "g5cxUb10HB1D0V1ErgVwssKsqg6rWLPj",
        "discovery": "http://'"$KEYCLOAK_ADDR"'/realms/gw/.well-known/openid-configuration",
        "introspection_endpoint_auth_method": "client_secret_basic",
        "realm": "gw",
        "bearer_only": false,
        "redirect_uri": "http://'"$SHENMA_ADDR"'/project-manage",
        "logout_path": "/logout",
        "redirect_login": true
      },
      "proxy-rewrite": {
        "regex_uri": ["^/project-manage/(.*)", "/$1"]
      }
    },
    "upstream": {
      "type": "roundrobin",
      "nodes": {
        "10.200.101.5:31000": 1
      }
    }
  }'

curl -i http://$APISIX_ADDR/apisix/admin/routes -H "$AUTH" -H "$TYPE" -X PUT -d '{
    "uri": "/completions/*",
    "id": "shenma",
    "upstream_id": "shenma",
    "plugins": {
      "limit-req": {
        "rate": 1,
        "burst": 0,
        "rejected_code": 503,
        "key": "remote_addr"
      },
      "openid-connect": {
        "client_id": "apisix",
        "client_secret": "g5cxUb10HB1D0V1ErgVwssKsqg6rWLPj",
        "discovery": "http://'"$KEYCLOAK_ADDR"'/realms/gw/.well-known/openid-configuration",
        "introspection_endpoint_auth_method": "client_secret_basic",
        "bearer_only": false,
        "realm": "gw",
        "redirect_uri": "http://'"$SHENMA_ADDR"'/completions/callback",
        "logout_path": "/completions/logout",
        "redirect_login": true
      }
    }
  }'
