version: '3.8'

services:
  apisix:
    image: apache/apisix:3.9.1-debian
    restart: always
    volumes:
      - ./apisix/config.yaml:/usr/local/apisix/conf/config.yaml:ro
    depends_on:
      - etcd
    ports:
      - "{{PORT_APISIX_API}}:9180/tcp"
      - "{{PORT_APISIX_ENTRY}}:9080/tcp"
      - "{{PORT_APISIX_PROMETHEUS}}:{{PORT_APISIX_PROMETHEUS}}/tcp"
    networks:
      - shenma

  apisix-dashboard:
    image: apache/apisix-dashboard:3.0.0-alpine
    restart: always
    volumes:
      - ./apisix_dashboard/conf.yaml:/usr/local/apisix-dashboard/conf/conf.yaml
    depends_on:
      - etcd
    ports:
      - "{{PORT_APISIX_DASHBOARD}}:{{PORT_APISIX_DASHBOARD}}/tcp"
    networks:
      - shenma

  etcd:
    image: bitnami/etcd:3.5.14
    restart: always
    volumes:
      - ./etcd/data:/bitnami/etcd/data
    user: "1000:1000"
    environment:
      ETCD_ENABLE_V2: "true"
      ALLOW_NONE_AUTHENTICATION: "yes"
      ETCD_ADVERTISE_CLIENT_URLS: "http://{{ZGSM_BACKEND}}:{{PORT_ETCD}}"
      ETCD_LISTEN_CLIENT_URLS: "http://0.0.0.0:{{PORT_ETCD}}"
    ports:
      - "{{PORT_ETCD}}:{{PORT_ETCD}}/tcp"
    networks:
      - shenma

  redis:
    image: docker.io/redis:7.2.4
    restart: always
    volumes:
      - ./redis/data:/data
    ports:
      - "{{PORT_REDIS}}:{{PORT_REDIS}}"
    networks:
      - shenma

  postgres:
    image: postgres:15-alpine
    restart: always
    environment:
      POSTGRES_DB: "keycloak"
      POSTGRES_USER: "keycloak"
      POSTGRES_PASSWORD: "password"
    volumes:
      - ./postgres/data:/var/lib/postgresql/data
    ports:
      - "{{PORT_POSTGRES}}:{{PORT_POSTGRES}}/tcp"
    networks:
      - shenma

  keycloak:
    image: quay.io/keycloak/keycloak:20.0.5
    command: ["start-dev"]
    restart: always
    environment:
      DB_ADDR: "{{ZGSM_BACKEND}}"
      DB_PORT: "{{PORT_POSTGRES}}"
      DB_VENDOR: "postgres"
      KEYCLOAK_ADMIN: "admin"
      KEYCLOAK_ADMIN_PASSWORD: "admin"
    ports:
      - "{{PORT_KEYCLOAK}}:8080/tcp"
    volumes:
      - ./keycloak/providers:/opt/keycloak/providers
      - ./keycloak/keycloak.conf:/opt/keycloak/conf/keycloak.conf:ro
    depends_on:
      - postgres
    networks:
      - shenma
    
  portal:
    image: nginx:1.27.1
    restart: always
    volumes:
      - ./portal/data:/var/www
      - ./portal/nginx.conf:/etc/nginx/nginx.conf
    ports:
      - "{{PORT_PORTAL}}:80/tcp"
    networks:
      - shenma

  trampoline:
    image: trampoline:1.0.241018
    restart: always
    volumes:
      - ./trampoline/data:/opt/trampoline/resources
    ports:
      - "{{PORT_TRAMPOLINE}}:8080/tcp"
    networks:
      - shenma

  chatgpt:
    image: docker.sangfor.com/containerd/chatgpt/server:1.5.9
    restart: always
    volumes:
      - ./chatgpt/logs:/server/logs
      - ./chatgpt/supervisor:/var/log/supervisor
      - ./chatgpt/local.yml:/server/config/local.yml
      - ./chatgpt/agent_chat.py:/server/services/agent_chat.py
      - ./chatgpt/analysis_manager.py:/server/third_platform/devops/analysis_manager.py
      - ./chatgpt/apiBot.py:/server/bot/apiBot.py
      - ./chatgpt/base_es.py:/server/third_platform/es/base_es.py
      - ./chatgpt/configuration_service.py:/server/services/system/configuration_service.py
      - ./chatgpt/events.py:/server/controllers/socket/events.py
      - ./chatgpt/application_context.py:/server/common/helpers/application_context.py
    ports:
      - "{{PORT_CHATGPT_API}}:5000/tcp"
      - "{{PORT_CHATGPT_WS}}:8765/tcp"
    environment:
      - TZ=Asia/Shanghai
      - CACHE_DB=chatgpt
      - REDIS_URL=redis://{{ZGSM_BACKEND}}:{{PORT_REDIS}}/0
      - SERVE_THREADS=200
      - SERVE_CONNECTION_LIMIT=512
      - PG_URL={{ZGSM_BACKEND}}:{{PORT_POSTGRES}}
      - DB_NAME=chatgpt
      - DATABASE_URI=postgresext+pool://keycloak:password@{{ZGSM_BACKEND}}/chatgpt
      - ES_SERVER=http://{{ZGSM_BACKEND}}:{{PORT_ES}}
      - ES_PASSWORD=4c6y4g6Z09T2w33pYRNKE3LG
      - DEVOPS_URL=
      - GEVENT_SUPPORT=True
      - NO_COLOR=1
      - DEPLOYMENT_TYPE=all
    depends_on:
      - redis
      - postgres
    networks:
      - shenma

  fauxpilot:
    image: docker.sangfor.com/moyix/copilot_proxy:1.5.9
    command: ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "5000"]
    restart: always
    volumes:
      - ./fauxpilot/logs:/python-docker/logs
      - ./fauxpilot/common.py:/python-docker/utils/common.py
    ports:
      - "{{PORT_FAUXPILOT}}:5000/tcp"
    environment:
      - TZ=Asia/Shanghai
      - THRESHOLD_SCORE=0.3
      - STR_PATTERN=import +.*|from +.*|from +.* import *.*
      - USER_CODE_UPLOAD_DELAY=30
      - MAX_MODEL_COST_TIME=3000
      - CONTEXT_LINES_LIMIT=1000
      - SNIPPET_TOP_N=0
      - MAX_MODEL_LEN=4000,2000
      - MAX_TOKENS=500
      - MULTI_LINE_STREAM_K=6
      - ENABLE_REDIS=False
      - REDIS_HOST={{ZGSM_BACKEND}}
      - REDIS_PORT={{PORT_REDIS}}
      - REDIS_DB=0
      - REDIS_PWD=""
      - MAIN_MODEL_TYPE=openai
      - OPENAI_MODEL_HOST={{OPENAI_MODEL_HOST}}
      - OPENAI_MODEL={{OPENAI_MODEL}}
    depends_on:
      - redis
    networks:
      - shenma

  prometheus:
    image: quay.io/prometheus/prometheus:v2.54.0
    restart: always
    volumes:
      - ./prometheus/prometheus.yml:/etc/prometheus/prometheus.yml
    ports:
      - "{{PORT_PROMETHEUS}}:9090"
    networks:
      - shenma

  grafana:
    image: docker.io/grafana/grafana:11.2.0
    restart: always
    ports:
      - "{{PORT_GRAFANA}}:3000"
    volumes:
      - "./grafana/provisioning:/etc/grafana/provisioning"
      - "./grafana/dashboards:/var/lib/grafana/dashboards"
      - "./grafana/config/grafana.ini:/etc/grafana/grafana.ini"
    networks:
      - shenma

  es:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.9.0
    environment:
      - discovery.type=single-node
      - bootstrap.memory_lock=true
      - xpack.security.enabled=false  # 禁用安全功能
      - xpack.security.http.ssl.enabled=false  # 禁用 HTTPS
      - "ES_JAVA_OPTS=-Xms512m -Xmx512m"
    user: "1000:1000"
    ulimits:
      memlock:
        soft: -1
        hard: -1
    ports:
      - "{{PORT_ES}}:9200"
      - "9300:9300"
    volumes:
      - ./es/data:/usr/share/elasticsearch/data
    networks:
      - shenma

networks:
  shenma:
    driver: bridge

