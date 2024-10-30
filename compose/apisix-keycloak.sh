#!/bin/sh

. apisix.conf.sh

#
# 三个上游：
#   portal-登录页面资源
#   trampoline-登录成功跳板
#   keycloak-登录整体逻辑
#

# 定义存放登录相关页面资源的upstream
curl -i http://$APISIX_ADDR/apisix/admin/upstreams -H "$AUTH" -H "$TYPE" -X PUT  -d '{
    "id": "portal",
    "nodes": {
        "'"$ZGSM_BACKEND:$PORT_PORTAL"'": 1
    },
    "type": "roundrobin"
}'

# 定义登录成功跳板(/login/ok)的upstream
curl -i http://$APISIX_ADDR/apisix/admin/upstreams -H "$AUTH" -H "$TYPE" -X PUT  -d '{
    "id": "trampoline",
    "nodes": {
        "'"$ZGSM_BACKEND:$PORT_TRAMPOLINE"'": 1
    },
    "type": "roundrobin"
}'

# 定义keycloak这个端点
curl -i http://$APISIX_ADDR/apisix/admin/upstreams -H "$AUTH" -H "$TYPE" -X PUT  -d '{
    "id": "keycloak",
    "nodes": {
        "'"$ZGSM_BACKEND:$PORT_KEYCLOAK"'": 1
    },
    "type": "roundrobin"
}'

# 把请求keycloak的请求定向到keycloak端点
curl -i  http://$APISIX_ADDR/apisix/admin/routes -H "$AUTH" -H "$TYPE" -X PUT -d '{
    "uris": ["/realms/'"$KEYCLOAK_REALM"'/*", "/resources/*"],
    "id": "keycloak",
    "upstream_id": "keycloak"
  }'

# 改写vscode认证请求返回的页面，将其中两个放在cdn上的JS文件重定向到zgsm.sangfor.com，因为这个cdn不稳定，容易失效
curl -i  http://$APISIX_ADDR/apisix/admin/routes -H "$AUTH" -H "$TYPE" -X PUT -d '{
    "uris": ["/realms/'"$KEYCLOAK_REALM"'/protocol/openid-connect/auth"],
    "id": "keycloak-auth",
    "upstream_id": "keycloak",
    "plugins": {
      "response-rewrite": {
        "filters":[
          {
            "regex":"https://cdn.jsdelivr.net/npm/vue/dist",
            "scope":"global",
            "replace":"/resources/e8cj8/login/phone/cdn"
          },
          {
            "regex":"https://cdn.jsdelivr.net/npm/axios/dist",
            "scope":"global",
            "replace":"/resources/e8cj8/login/phone/cdn"
          }
        ]
      }
    }
  }'

# 登录页需要用到的图片:img/keycloak-bg.png,img/favicon.ico,css/login.css
curl -i  http://$APISIX_ADDR/apisix/admin/routes -H "$AUTH" -H "$TYPE" -X PUT -d '{
    "uris": ["/resources/e8cj8/login/phone/*"],
    "id": "keycloak-auth-resource",
    "upstream_id": "portal",
    "plugins": {
      "proxy-rewrite": {
        "regex_uri": ["^/resources/e8cj8/login/phone/(. *)", "/login/$1"]
      }
    }
  }'

# 登录页的css文件
curl -i  http://$APISIX_ADDR/apisix/admin/routes -H "$AUTH" -H "$TYPE" -X PUT -d '{
    "uris": ["/resources/e8cj8/login/phone/css/login.css"],
    "id": "keycloak-login-css",
    "upstream_id": "portal",
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

# 将登录成功后的跳板请求转发给trampoline服务
curl -i  http://$APISIX_ADDR/apisix/admin/routes -H "$AUTH" -H "$TYPE" -X PUT -d '{
    "uris": ["/login/ok", "/login/resources/*"],
    "id": "keycloak-trampoline",
    "upstream_id": "trampoline"
  }'

