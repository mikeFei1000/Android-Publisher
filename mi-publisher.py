#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os

from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_v1_5
from cryptography.x509 import load_pem_x509_certificate
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives._serialization import Encoding
from cryptography.hazmat.primitives._serialization import PublicFormat
from requests_toolbelt import MultipartEncoder
import json
import hashlib
import requests
import sys
import utils


# 应用推送接口
def pushApp(file_path):
    global DOMAIN
    url = DOMAIN + "/dev/push"
    config = json.load(open("config.json", 'r'))
    updateDesc = utils.readFile("release-note-zh-CN.txt")
    appInfo = {"appName": config["appName"], "packageName": config["packageName"], "updateDesc": updateDesc}
    requestData = json.dumps({"userName": config["xiaomi"]["user_name"], "synchroType": 1, "appInfo": appInfo},
                             ensure_ascii=False)
    print(requestData)
    m = MultipartEncoder(
        fields={'apk': (os.path.basename(file_path), open(file_path, 'rb'), 'application/octet-stream'),
                'RequestData': requestData,
                'SIG': getSIGRequestDataJson(requestData, file_path)}
    )
    headers = {
        "Content-Type": m.content_type
    }
    result = requests.post(url, m, headers=headers)
    print(result.json())


def arrayCopy(src, src_pos, dest, dest_pos, length):
    for i in range(length):
        dest[i + dest_pos] = src[i + src_pos]


DOMAIN = "http://api.developer.xiaomi.com/devupload"
KEY_SIZE = 1024
GROUP_SIZE = 128
ENCRYPT_GROUP_SIZE = GROUP_SIZE - 11


# 传递请求参数获取 SIG 签名
def getSIGRequestDataJson(requestDataJson, apkPath):
    hash_list = [{"name": "RequestData", "hash": hashlib.md5(requestDataJson.encode(encoding='utf-8')).hexdigest()}]
    if len(apkPath) != 0:
        apkMD5 = utils.getFileMD5(apkPath)
        if len(apkMD5) != 0:
            hash_list.append({"name": "apk", "hash": apkMD5})
    return getSIG(hash_list, json.load(open("config.json", 'r'))["xiaomi"]["private_key"])


# SIG 数字签名的生成方法
def getSIG(sigData, privateKey):
    sig = json.dumps({"sig": sigData, "password": privateKey}, ensure_ascii=False)
    print(sig)
    with open('dev.api.public.cer', 'rb') as f:
        buff = f.read()
    cert_obj = load_pem_x509_certificate(buff, default_backend())
    public_key = cert_obj.public_key()
    pk = public_key.public_bytes(encoding=Encoding.PEM, format=PublicFormat.PKCS1)
    cipher_public = PKCS1_v1_5.new(RSA.importKey(pk))
    text_bytes = sig.encode('UTF-8')
    text_bytes_len = len(text_bytes)
    idx = 0
    encrypt_bytes = bytearray()
    while idx < text_bytes_len:
        remain = text_bytes_len - idx
        if remain > ENCRYPT_GROUP_SIZE:
            segsize = ENCRYPT_GROUP_SIZE
        else:
            segsize = remain
        segment = bytearray(segsize)
        arrayCopy(text_bytes, idx, segment, 0, segsize)
        encrypt_bytes = encrypt_bytes + cipher_public.encrypt(segment)
        idx += segsize
    return encrypt_bytes.hex()


if __name__ == '__main__':
    pushApp(sys.argv[1])