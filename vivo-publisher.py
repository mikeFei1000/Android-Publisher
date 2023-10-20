import hashlib
import hmac
import json
import sys
import time

import requests
import utils

config = json.load(open("config.json", 'r'))
# 沙箱环境api调用地址
# domain = "https://sandbox-developer-api.vivo.com.cn/router/rest"
# 正式环境api调用地址
domain = "https://developer-api.vivo.com.cn/router/rest"
# 申请API服务后平台分配的accessKey
access_key = config["vivo"]["access_key"]
# 申请API服务后平台分配的accessSecret
access_secret = config["vivo"]["access_secret"]
# 签名算法(当前支持HMAC-SHA256)
sign_method = "HMAC-SHA256"
# api版本
api_version = "1.0"
# 返回数据类型(当前支持json)
data_format = "json"
# 接口目标类型, 接口传包必须使用developer
target_app_key = "developer"
# 更新apk包上传接口名称
api_upload_method = "app.upload.apk.app"
# 应用同步更新接口名称
update_app_method = "app.sync.update.app"

submit_review_result_path = "vivoResult/submitReviewResult.txt"

upload_app_result_path = "vivoResult/uploadAppResult.txt"


# 计算签名
def cal_sign(access_secret, request_body):
    # 请求参数按key排序
    keys = request_body.keys()
    keys_list = []
    for key in keys:
        keys_list.append(key)
    keys_list.sort()

    # 拼接参数
    sign_params = []
    for key in keys_list:
        param = str(key) + "=" + str(request_body[key])
        sign_params.append(param)
    sign_data = "&".join(sign_params)

    # 算签名
    signature = hmac.new(access_secret.encode('utf-8'), sign_data.encode('utf-8'), hashlib.sha256).hexdigest()
    return signature


def getDefaultParams():
    return {
        # 公共参数
        "access_key": access_key,
        "target_app_key": target_app_key,
        "v": api_version,
        "format": data_format,
        "sign_method": sign_method,
        "timestamp": int(round(time.time() * 1000)),
    }


def uploadApp(file_path):
    request_body = getDefaultParams()
    request_body['packageName'] = config["packageName"]
    # method是调用的具体业务方法, 可以查看某个详细的业务接口获取, eg：https://dev.vivo.com.cn/documentCenter/doc/342
    request_body['method'] = api_upload_method
    # 业务参数: 可以查看某个详细业务接口文档获得, eg: https://dev.vivo.com.cn/documentCenter/doc/342
    request_body['fileMd5'] = utils.getFileMD5(file_path)
    sign = cal_sign(access_secret, request_body)
    request_body['sign'] = sign
    # file不参与sign计算，需要在sign计算后加入
    files = {
        "file": open(file_path, 'rb')
    }
    response = requests.post(domain, data=request_body, files=files)
    resultJson = response.json()
    print("Response body:{0}".format(resultJson))
    utils.writeFile(upload_app_result_path, response.text)
    # 返回数据
    return resultJson


def submitReview(resultJson):
    request_body = getDefaultParams()
    request_body['packageName'] = config["packageName"]
    request_body['method'] = update_app_method
    request_body['versionCode'] = resultJson['data']['versionCode']
    request_body['apk'] = resultJson['data']['serialnumber']
    request_body['fileMd5'] = resultJson['data']['fileMd5']
    # 实时上架
    request_body['onlineType'] = 1
    request_body['updateDesc'] = utils.readFile("release-note-zh-CN.txt")
    sign = cal_sign(access_secret, request_body)
    request_body['sign'] = sign
    response = requests.post(domain, data=request_body)
    resultJson = response.json()
    print("Response body:{0}".format(resultJson))
    utils.writeFile(submit_review_result_path, response.text)
    # 返回数据
    return resultJson


if __name__ == '__main__':
    result = uploadApp(sys.argv[1])
    if result["code"] == 0 and result["subCode"] == '0':
        submitResult = submitReview(result)
        if submitResult["code"] != 0 or submitResult["subCode"] != '0':
            print("vivo 提交更新时出错了，msg:{},详细日志查看:{}".format(submitResult['msg'], submit_review_result_path))
        else:
            print("vivo 提交更新成功")
    else:
        print("vivo 上传 apk 出错了，msg: {},详细日志查看:{}".format(result['msg'], upload_app_result_path))
