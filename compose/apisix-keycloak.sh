#!/bin/sh

AUTH="X-API-KEY: edd1c9f034335f136f87ad84b625c8f1" 
TYPE="Content-Type: application/json"
APISIX_ADDR="172.16.0.2:9180"

# 定义keycloak这个端点
curl -i http://$APISIX_ADDR/apisix/admin/upstreams -H "$AUTH" -H "$TYPE" -X PUT  -d '{
    "id": "keycloak",
    "nodes": {
        "172.16.0.2:8080": 1
    },
    "type": "roundrobin"
}'

# 把请求keycloak的请求定向到keycloak端点
curl -i  http://$APISIX_ADDR/apisix/admin/routes -H "$AUTH" -H "$TYPE" -X PUT -d '{
    "uris": ["/realms/gw/*", "/resources/iodim/*"],
    "id": "keycloak",
    "upstream_id": "keycloak"
  }'

# 改写vscode认证请求返回的页面，将其中两个放在cdn上的JS文件重定向到zgsm.sangfor.com，因为这个cdn不稳定，容易失效
curl -i  http://$APISIX_ADDR/apisix/admin/routes -H "$AUTH" -H "$TYPE" -X PUT -d '{
    "uris": ["/realms/gw/protocol/openid-connect/auth"],
    "id": "keycloak-auth",
    "upstream_id": "keycloak",
    "plugins": {
      "response-rewrite": {
        "filters":[
          {
            "regex":"https://cdn.jsdelivr.net/npm/vue/dist",
            "scope":"global",
            "replace":"/login/cdn"
          },
          {
            "regex":"https://cdn.jsdelivr.net/npm/axios/dist",
            "scope":"global",
            "replace":"/login/cdn"
          }
        ]
      }
    }
  }'

# 将上述重定向的js请求转发给portal-web服务，由其返回对应的js文件
curl -i  http://$APISIX_ADDR/apisix/admin/routes -H "$AUTH" -H "$TYPE" -X PUT -d '{
    "uris": ["/login/cdn/*", "/login/img/*", "/login/css/*"],
    "id": "keycloak-login-cdn",
    "upstream": {
        "type": "roundrobin",
        "nodes": {
            "172.16.0.2:9081": 1
        }
    }
  }'

# 登录页需要用到的图片:img/keycloak-bg.png,img/favicon.ico
curl -i  http://$APISIX_ADDR/apisix/admin/routes -H "$AUTH" -H "$TYPE" -X PUT -d '{
    "uris": ["/resources/iodim/login/phone/img/*"],
    "id": "keycloak-login-img",
    "upstream": {
        "type": "roundrobin",
        "nodes": {
            "172.16.0.2:9081": 1
        }
    },
    "plugins": {
      "proxy-rewrite": {
        "regex_uri": ["^/resources/iodim/login/phone/img/(. *)", "/login/img/$1"]
      }
    }
  }'

# 登录页的css文件
curl -i  http://$APISIX_ADDR/apisix/admin/routes -H "$AUTH" -H "$TYPE" -X PUT -d '{
    "uris": ["/resources/iodim/login/phone/css/login.css"],
    "id": "keycloak-login-css",
    "upstream": {
        "type": "roundrobin",
        "nodes": {
            "172.16.0.2:9081": 1
        }
    },
    "plugins": {
      "proxy-rewrite": {
        "uri": "/login/css/login.css"
      },
      "response-rewrite": {
        "headers": {
          "set": {
            "Content-Type": "text/css;charset=UTF-8",
            "Cache-Control": "no-cache"
          }
        }
      }
    }
  }'
