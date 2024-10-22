#!/bin/sh

# 获取访问令牌
CLIENT_ID="vscode"
CLIENT_SECRET="jFWyVy9wUKKSkX55TDBt2SuQWl7fDM1l"
TOKEN_ENDPOINT="https://zgsm.sangfor.com/realms/gw/protocol/openid-connect/token"
AUTHORIZATION_ENDPOINT="https://zgsm.sangfor.com/realms/gw/protocol/openid-connect/auth"
INFERENCE_ENDPOINT="https://zgsm.sangfor.com/v2/completions"
REDIRECT_URI="https://zgsm.sangfor.com/callback"
SCOPE="openid profile email"
STATE="012345678"
FILE="./access_token"

ACCESS_TOKEN=""
if [ -f "$FILE" ]; then
  # 读取文件内容到变量ACCESS_TOKEN中
  ACCESS_TOKEN=$(cat "$FILE")
else
  # 步骤1：获取授权码
  echo "请在浏览器中打开以下URL并授权："
  AUTH_URL="${AUTHORIZATION_ENDPOINT}?response_type=code&client_id=${CLIENT_ID}&redirect_uri=${REDIRECT_URI}&scope=${SCOPE}&state=${STATE}"
  echo $AUTH_URL

  # 提示用户输入授权码
  read -p "请输入从重定向URL中获取的授权码: " AUTH_CODE

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
RSP=`curl -k -i -X POST -H "Authorization: Bearer $ACCESS_TOKEN" -H "Content-Type: application/json" $INFERENCE_ENDPOINT -d '{
     "model": "DeepSeek-Coder-V2-Lite-Base",
     "prompt": "def hello"
   }'`

echo $RSP
echo $RSP | grep 'HTTP/1.1 401 Unauthorized' && echo Unauthorized, please remove ./access_token and retry it && exit 1
echo $RSP | grep 'HTTP/1.1 200' && echo Succeeded && exit 0
