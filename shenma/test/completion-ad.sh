#!/bin/sh

TYPE="Content-Type: application/json"
HOST="172.16.254.5"
PORT="32080"
TEMP='{
  "model": "DeepSeek-Coder-V2-Lite-Base",
  "prompt": "#!/usr/bin/env python\n# coding: utf-8\nimport time\nimport base64\nfrom Crypto.Cipher import AES\nimport requests\ndef trace(rsp):\n    print",
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
  PORT="$1"
fi

if [ X"$2" != X"" ]; then
  DATA=`jq --arg newValue "$(cat $2)" '.prompt = $newValue' <<< "$TEMP"`
else
  DATA="$TEMP"
fi

echo ADDR: http://$HOST:$PORT/v2/completions
echo DATA: $DATA

curl -i http://$HOST:$PORT/v2/completions -H "$TYPE" -X POST -d "$DATA"

curl -i http://$HOST:$PORT/v2/completions -H "$TYPE" -X POST -d "$DATA"