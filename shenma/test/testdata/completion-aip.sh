#!/bin/sh

TYPE="Content-Type: application/json"
HOST="10.72.1.16"
PORT="32322"

if [ X"$1" != X"" ]; then
  PORT="$1"
fi

echo ADDR: http://$HOST:$PORT/v1/completions

curl -i http://$HOST:$PORT/v1/completions -H "$TYPE" -X POST  -d '{
  "model": "DeepSeek-Coder-V2-Lite-Base",
  "prompt": "#!/usr/bin/env python\n# coding: utf-8\n# author：钱锴19648(感谢大佬分享)\nimport time\nimport base64\nfrom Crypto.Cipher import AES\nimport requests\ndef trace(rsp):\n    print"
}'