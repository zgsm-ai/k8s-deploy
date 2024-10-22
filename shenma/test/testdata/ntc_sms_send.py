#!/usr/bin/env python
# coding: utf-8
# author：钱锴19648(感谢大佬分享)
import time
import base64
from Crypto.Cipher import AES
import requests

def trace(rsp):
    print("Request URL:", rsp.request.url)
    print("Request Method:", rsp.request.method)
    print("Request Headers:", rsp.request.headers)
    print("Request Body:", rsp.request.body)

    # 输出响应的详细信息
    print("Response Status Code:", rsp.status_code)
    print("Response Headers:", rsp.headers)
    print("Response Content:", rsp.text)
    
def get_token():
    BS = 16
    pad = lambda s: s + (BS - len(s) % BS) * chr(BS - len(s) % BS)
    # 应用加密Key
    my_secret = "a80982a50d0b4f7a98db6b91fdaf34ae"
    # 偏移量
    iv = "TRYTOCN314402233"

    # 计算当前时间戳，精确到毫秒
    t = time.time()
    timestamp = str(int(round(t * 1000)))

    # 需要加密的字符串
    text = pad('{"clientId": "1724993521440","timesstamp": %s}' % timestamp).encode()

    cipher = AES.new(my_secret.encode(), AES.MODE_CBC, iv.encode())  # 加密函数  密钥 模式 偏移量
    login_code = base64.urlsafe_b64encode(cipher.encrypt(text)).decode('utf-8')  # 先加密再重新编码
    # url = f"http://it-gw.sangfor.com/api/api-auth/oauth/get/jwttoken?loginCode={login_code}&clientId=1724993521440"
    url = "http://it-gw.sangfor.com/api/api-auth/oauth/get/jwttoken?loginCode={}&clientId=1724993521440".format(login_code)
    payload = {}
    headers = {}

    response = requests.request("POST", url, headers=headers, data=payload)
    trace(response)
    return response.json()["rows"]["access_token"]


def send_sms(user_list, title, msg):
    url = "http://it-gw.sangfor.com/ntc/sms/sendSms"
    token = get_token()
    headers = {
        "authorization": token,
        "Content-Type": "application/json"
    }

    # 把user_list转换成字符串
    sendTo = ""
    for user in user_list:
        if sendTo != "":
            sendTo += ","
        sendTo += user
    content = title + "\n" + msg
    data = {
        "systemCode": "shenma",
        "phone": sendTo,
        "systemCodePrefix": "0",
        "content": content
    }

    response = requests.post(url, headers=headers, json=data, timeout=5)
    trace(response)
    return response.json()

# # author：廖磊57452(感谢大佬分享)
# def intranet_mail_send_msg(recipient_list, subject, msg):
#     token = get_token()
#     url = "http://it-gw-sit.sangfor.com/ntc/mail/lanSendMail"
#     headers = {
#         "authorization": token,
#         "Content-Type": "application/json"
#     }

#     # 把user_list转换成字符串
#     recipient = ""
#     for element in recipient_list:
#         recipient += element
#         recipient += ","

#     data = {
#         "systemCode": "achktest",
#         "recipient": recipient,
#         "subject": subject,
#         "content": msg,
#         "fromName": "自动化测试",
#     }
#     response = requests.post(url, headers=headers, json=data)
#     print(response.json())


if __name__ == '__main__':
    # intranet_mail_send_msg(recipient_list=["57452@sangfor.com"], subject="新春快乐", msg="新年快乐恭喜发财")
    print(send_sms(user_list=["13824366192"], title="323901", msg="此认证码由诸葛神码发送，请勿泄露"))

if 