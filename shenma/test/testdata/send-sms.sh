#!/bin/sh

curl -i http://it-gw.sangfor.com/ntc/sms/sendSms -X POST -d '{
  "systemCode": "shenma",
  "phone": "13824366192",
  "systemCodePrefix": "0",
  "content": "恭喜发财"
}'

curl 