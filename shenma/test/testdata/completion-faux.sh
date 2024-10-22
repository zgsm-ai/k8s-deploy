#!/bin/sh

FAUX_ADDR="http://zgsm.sangfor.com/v2/completions"
FILE="./access_token"

ACCESS_TOKEN="eyJhbGciOiJSUzI1NiIsInR5cCIgOiAiSldUIiwia2lkIiA6ICJCVS1HUWZvdjk5WnBXckhYbjRGMlZ3U1hXMzBqbTNaY3JFRFVEM1BiaGhBIn0.eyJleHAiOjE3MjY3OTkwNjQsImlhdCI6MTcyNjc5Nzg2NCwiYXV0aF90aW1lIjoxNzI2Nzk1MTU3LCJqdGkiOiI1ZTNmNThkNS0zYTg5LTQzYWEtYWQ2ZS00MWM2ZTI4ZGRlYmMiLCJpc3MiOiJodHRwczovL3pnc20uc2FuZ2Zvci5jb20vcmVhbG1zL2d3IiwiYXVkIjoiYWNjb3VudCIsInN1YiI6IjMwYTA3NGE3LTM4ZTktNGY0Ny1iZWMwLTRlYjBlYmY3MjE2YSIsInR5cCI6IkJlYXJlciIsImF6cCI6InZzY29kZSIsInNlc3Npb25fc3RhdGUiOiIxNzIwZmI2NS03ZmRlLTQ0OGQtYTRmNC03MDQwOTdlNzE3NmEiLCJhY3IiOiIxIiwiYWxsb3dlZC1vcmlnaW5zIjpbImh0dHBzOi8vemdzbS5zYW5nZm9yLmNvbSJdLCJyZWFsbV9hY2Nlc3MiOnsicm9sZXMiOlsib2ZmbGluZV9hY2Nlc3MiLCJ1bWFfYXV0aG9yaXphdGlvbiIsImRlZmF1bHQtcm9sZXMtZ3ciXX0sInJlc291cmNlX2FjY2VzcyI6eyJhY2NvdW50Ijp7InJvbGVzIjpbIm1hbmFnZS1hY2NvdW50IiwibWFuYWdlLWFjY291bnQtbGlua3MiLCJ2aWV3LXByb2ZpbGUiXX19LCJzY29wZSI6Im9wZW5pZCBwaG9uZSBlbWFpbCBwcm9maWxlIiwic2lkIjoiMTcyMGZiNjUtN2ZkZS00NDhkLWE0ZjQtNzA0MDk3ZTcxNzZhIiwiZW1haWxfdmVyaWZpZWQiOmZhbHNlLCJwcmVmZXJyZWRfdXNlcm5hbWUiOiJ6YmMiLCJnaXZlbl9uYW1lIjoiIiwiZmFtaWx5X25hbWUiOiIiLCJlbWFpbCI6InpiY0BzYW5nZm9yLmNvbS5jbiJ9.HgOpfYXNlACy_AYwLp1ztVjMoYtojLwnkpwTpvb1j2KWJpzmRYNCJhkbNmA4MTmPfuZkEJUFX0tMnDP0zmSKCvoYrssVLZiA49xIz7N2kU-zXnwb5vOBjkb_cN4zr2vVve1Wc2zBenNicJkdXBRAYYkyTQ4KkqamchhZ_aDoqGuDxzVMcojMT5sJnPka2XU8Gv-2vtfab2xpIOF9CWaAbd44wBrNeyOwNOa4k3vDcjMsTBPt7hB4kmJIl55XqCLU6S9K7kCDP05J3EpogYSjU4vEtsT5rFP-NUo5RI7eiLN8v4fgCGFWX9Nv4O9PxyRCqVoa2NdhPYk24GptfZtNZQ"
if [ -f "$FILE" ]; then
  # 读取文件内容到变量ACCESS_TOKEN中
  ACCESS_TOKEN=$(cat "$FILE")
fi

AUTH="Authorization: Bearer $ACCESS_TOKEN"
TYPE="Content-Type: application/json"
DATA='{
  "model": "DeepSeek-Coder-V2-Lite-Base",
  "prompt": "def "
}'

if [ X"$1" != X"" ]; then
  DATA=`jq --arg newValue "$(cat $1)" '.prompt = $newValue' <<< '{"model": "DeepSeek-Coder-V2-Lite-Base","prompt": ""}'`
fi

echo FAUXPILOT: $FAUX_ADDR
echo AUTH: $AUTH
echo DATA: "$DATA"

curl -k -i $FAUX_ADDR -H "$AUTH" -H "$TYPE" -X POST  -d "$DATA"