#!/bin/sh

# 检查./access_token的合法性
# 如果没有./access_token，则发起认证流程，获取合法的access_token

HOST=""
PORT=""
ADDR=""

function print_help() {
  echo "Usage: $0 [-H host] [-p port] [-a addr]"
  echo "  -H host: 主机"
  echo "  -p port: 端口"
  echo "  -a addr: 地址"
  echo "  -h: 帮助"
}
# 初始化选项
while getopts "p:a:H:h" opt; do
  case "$opt" in
    p) 
      PORT="$OPTARG"
      ;;
    a)
      ADDR="$OPTARG"
      ;;
    H)
      HOST="$OPTARG"
      ;;
    h)
      print_help
      exit 0
      ;;
    *) 
      echo "无效选项"
      print_help
      exit 1
      ;;
  esac
done

if [ X"$ADDR" == X"" ]; then
  if [ X"$HOST" == X"" -a X"$PORT" == X"" ]; then
    ADDR="https://zgsm.sangfor.com"
  else
    if [ X"$HOST" == X"" ]; then
      HOST="172.16.0.4"
    fi
    if [ X"$PORT" == X"" ]; then
      PORT="9080"
    fi
    ADDR="http://$HOST:$PORT"
  fi
fi

ORIGIN_REDIECT_URI="$ADDR/realms/gw/login-actions/authenticate?client_id=vscode&redirect_uri=vscode://zgsm-ai.zgsm/callback"
REDIRECT_URI=$(printf '%s' "$ORIGIN_REDIECT_URI" | jq -sRr @uri)

# 获取访问令牌
CLIENT_ID="vscode"
CLIENT_SECRET="jFWyVy9wUKKSkX55TDBt2SuQWl7fDM1l"
SCOPE="openid profile email"
STATE="012345678"
FILE="./access_token"
TOKEN_ENDPOINT="$ADDR/realms/gw/protocol/openid-connect/token"
AUTH_ENDPOINT="$ADDR/realms/gw/protocol/openid-connect/auth"
APP_ENDPOINT="$ADDR/v2/completions"

ACCESS_TOKEN=""
if [ -f "$FILE" ]; then
  # 读取文件内容到变量ACCESS_TOKEN中
  ACCESS_TOKEN=$(cat "$FILE")
else
  # 步骤1：获取授权码
  echo "请在浏览器中打开以下URL并授权："
  AUTH_URL="${AUTH_ENDPOINT}?response_type=code&client_id=${CLIENT_ID}&redirect_uri=${REDIRECT_URI}&scope=${SCOPE}&state=${STATE}"
  echo $AUTH_URL

  # 提示用户输入授权码
  read -p "请输入从重定向URL中获取的授权码(即code字段): " AUTH_CODE

  # 步骤2：使用授权码获取访问令牌
  RESPONSE=$(curl -k -s -X POST $TOKEN_ENDPOINT \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "grant_type=authorization_code" \
    -d "client_id=$CLIENT_ID" \
    -d "client_secret=$CLIENT_SECRET" \
    -d "code=$AUTH_CODE" \
    -d "redirect_uri=$REDIRECT_URI")

  # 解析访问令牌
  ACCESS_TOKEN=$(echo $RESPONSE | jq -r '.access_token')

  # 检查是否成功获取访问令牌
  if [ "$ACCESS_TOKEN" == "null" ]; then
    echo "获取访问令牌失败：$RESPONSE"
    exit 1
  fi
  echo $ACCESS_TOKEN > ./access_token
fi

echo "访问令牌: $ACCESS_TOKEN"

# 使用访问令牌访问受保护的资源
# 使用令牌发送请求
RSP=`curl -k -i -X POST -H "Authorization: Bearer $ACCESS_TOKEN" -H "Content-Type: application/json" $APP_ENDPOINT -d '{
     "model": "DeepSeek-Coder-V2-Lite-Base",
     "prompt": "def hello"
   }'`

echo $RSP
echo $RSP | grep 'HTTP/1.1 401 Unauthorized' && echo Unauthorized, please remove ./access_token and retry it && exit 1
echo $RSP | grep 'HTTP/1.1 200' && echo Succeeded && exit 0


