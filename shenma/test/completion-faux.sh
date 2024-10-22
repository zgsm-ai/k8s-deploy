#!/bin/sh

FAUX_ADDR="http://zgsm.sangfor.com/v2/completions"
FILE="./access_token"

ACCESS_TOKEN=""
if [ -f "$FILE" ]; then
  # 读取文件内容到变量ACCESS_TOKEN中
  ACCESS_TOKEN=$(cat "$FILE")
else
  echo Please run ./verify-auth.sh first!
  exit 1
fi

AUTH="Authorization: Bearer $ACCESS_TOKEN"
TYPE="Content-Type: application/json"
DATA='{
  "model": "DeepSeek-Coder-V2-Lite-Base",
  "prompt": "def ",
  "temperature": 0.1,
  "stop": [],
  "language_id": "python",
  "beta_mode": "false",
  "trigger_mode": "manual",
  "headers": {
      "ide": "vscode",
      "ide-version": "1.4.0",
      "ide-real-version": "1.82.0"
  },
  "user_id": "",
  "repo": "",
  "git_path": ""
}'

if [ X"$1" != X"" ]; then
  DATA=`jq --arg newValue "$(cat $1)" '.prompt = $newValue' <<< '{"model": "DeepSeek-Coder-V2-Lite-Base","prompt": ""}'`
fi

echo FAUXPILOT: $FAUX_ADDR
echo AUTH: $AUTH
echo DATA: "$DATA"

curl -k -i $FAUX_ADDR -H "$AUTH" -H "$TYPE" -X POST  -d "$DATA"
