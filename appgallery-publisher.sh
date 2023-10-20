#!/usr/bin/env bash
#$(find ../app/build/apks/longbridgeOnline -name '*AO000004.apk')
file_path=${1}
huawei_filename=$(echo $file_path | xargs basename)
file_suffix=$(echo $huawei_filename | sed 's/.*\.//') # APK, RPK, PDF, JPG, JPEG, PNG, BMP, MP4, MOV, and AAB
show_debug_logs="no"
huawei_app_id=$(jq -r '.appgallery.appId' config.json)
huawei_client_id=$(jq -r '.appgallery.client_id' config.json)
huawei_client_secret=$(jq -r '.appgallery.client_secret' config.json)
release_type=$(jq -r '.appgallery.releaseType' config.json) #应用发布方式默认值为1全网3分阶段
token_json="appgalleryResult/token.json"
app_info_json="appgalleryResult/appInfo.json"
upload_result_json="appgalleryResult/uploadurl.json"
upload_file_result_json="appgalleryResult/uploadfile.json"
update_file_result_json="appgalleryResult/result.json"
submit_result_json="appgalleryResult/resultSubmission.json"
set -e # fail if any commands fails
if [ "${show_debug_logs}" == "yes" ]; then
  set -x # 设置-x选项后，之后执行的每一条命令，都会显示的打印出来
fi

## 1. GET TOKEN
function getToken() {
  printf "\n\nObtaining a Token\n"

  curl --silent -X POST \
    https://connect-api.cloud.huawei.com/api/oauth2/v1/token \
    -H 'Content-Type: application/json' \
    -H 'cache-control: no-cache' \
    -d '{
      "grant_type": "client_credentials",
      "client_id": "'${huawei_client_id}'",
      "client_secret": "'${huawei_client_secret}'"
  }' > ${token_json}

  printf "\nObtaining a Token ✅\n"
}

## 2. GET APP INFO
function getAppInfo() {
    ACCESS_TOKEN=$(readAccessToken)
    curl --silent -X GET \
      'https://connect-api.cloud.huawei.com/api/publish/v2/app-info?appId='"${huawei_app_id}"'' \
      -H 'Authorization: Bearer '"${ACCESS_TOKEN}"'' \
      -H 'Content-Type: application/json' \
      -H 'client_id: '"${huawei_client_id}"'' > ${app_info_json}
}

# 3.update release note
function updateNewFeatures() {
  jq -r '.languages[].lang' ${app_info_json} | while read lang; do
    file_path="release-note-${lang}.txt"
    if [ -f ${file_path} ];then
      updateNewFeaturesForEach ${lang} $(cat ${file_path})
    else
      echo "${lang}文件不存在"
    fi
  done
}

function updateNewFeaturesForEach() {
  if [[ -n ${2} ]]; then
    ACCESS_TOKEN=$(readAccessToken)
    curl --silent -X PUT \
      'https://connect-api.cloud.huawei.com/api/publish/v2/app-language-info?appId='"${huawei_app_id}"'' \
      -H 'Authorization: Bearer '"${ACCESS_TOKEN}"'' \
      -H 'Content-Type: application/json' \
      -H 'client_id: '"${huawei_client_id}"'' \
      -d '{"lang": "'${1}'",
          "newFeatures":"'"${2}"'"
        }' > "appgalleryResult/resultNewFeatures${1}.json"
  fi
}

## 4. GET Upload URL and authCode
function getFileUploadUrl() {
  ACCESS_TOKEN=$(readAccessToken)

  printf "\nObtaining the File Upload URL\n"

  curl --silent -X GET \
    'https://connect-api.cloud.huawei.com/api/publish/v2/upload-url?appId='"${huawei_app_id}"'&suffix='"${file_suffix}"'&releaseType='"${release_type}" \
    -H 'Authorization: Bearer '"${ACCESS_TOKEN}"'' \
    -H 'client_id: '"${huawei_client_id}"'' > ${upload_result_json}

  printf "\nObtaining the File Upload URL ✅\n"
}

## 5. Upload file, -F implicitly means Content-Type: multipart/form-data
function uploadFile() {
  UPLOAD_URL=$(jq -r '.uploadUrl' ${upload_result_json})
  UPLOAD_AUTH_CODE=$(jq -r '.authCode' ${upload_result_json})

  printf "\nUploading a File\n"

  curl --silent -X POST \
    "${UPLOAD_URL}" \
    -H 'Accept: application/json' \
    -F authCode="${UPLOAD_AUTH_CODE}" \
    -F fileCount=1 \
    -F file="@${file_path}" > ${upload_file_result_json}

  printf "\nUploading a File ✅\n"
}

## 6. Updating App File Information
function updateAppFileInfo() {
  ACCESS_TOKEN=$(readAccessToken)
  FILE_DEST_URL=$(jq -r '.result.UploadFileRsp.fileInfoList[0].fileDestUlr' ${upload_file_result_json})

  printf "\nUpdating App File Information - With the previoulsy uploaded file: ${huawei_filename}"

  curl --silent -X PUT \
    'https://connect-api.cloud.huawei.com/api/publish/v2/app-file-info?appId='"${huawei_app_id}"'' \
    -H 'Authorization: Bearer '"${ACCESS_TOKEN}"'' \
    -H 'Content-Type: application/json' \
    -H 'client_id: '"${huawei_client_id}"'' \
    -H 'releaseType: '"${release_type}"'' \
    -d '{
    "fileType":5,
    "files":[
      {
        "fileName":"'${huawei_filename}'",
        "fileDestUrl":"'"${FILE_DEST_URL}"'"
      }]
  }' > ${update_file_result_json}

  printf "\nUpdating App File Information - With the previoulsy uploaded file ✅"
}

# 7.submit app review
function submitApp() {
  #软件包采用异步解析方式，请您在传包后等候2分钟再调用提交发布接口
  printf "Waiting 3 minutes for upload to get processed...\n"
  sleep 180
  if [ "${release_type}" == "3" ]; then
    submitAppPhaseMode
  else
    submitAppDirectly
  fi
}

function submitAppPhaseMode() {
  ACCESS_TOKEN=$(readAccessToken)
  JSON_STRING="{\"phasedReleaseStartTime\":\"$phase_release_start_time+0000\",\"phasedReleaseEndTime\":\"$phase_release_end_time+0000\",\"phasedReleaseDescription\":\"$phase_release_description\",\"phasedReleasePercent\":\"$phase_release_percentage\"}"

  curl --silent -X POST \
    'https://connect-api.cloud.huawei.com/api/publish/v2/app-submit?appid='"${huawei_app_id}"'&releaseType='"${release_type}" \
    -H 'Authorization: Bearer '"${ACCESS_TOKEN}"'' \
    -H 'Content-Type: application/json' \
    -H 'client_id: '"${huawei_client_id}"'' \
    -d "${JSON_STRING}" > ${submit_result_json}
}

function submitAppDirectly() {
  ACCESS_TOKEN=$(readAccessToken)

  curl --silent -X POST \
    'https://connect-api.cloud.huawei.com/api/publish/v2/app-submit?appid='"${huawei_app_id}"'' \
    -H 'Authorization: Bearer '"${ACCESS_TOKEN}"'' \
    -H 'client_id: '"${huawei_client_id}"'' > ${submit_result_json}
}

function readAccessToken() {
    echo $(jq -r '.access_token' ${token_json})
}

function mkResultDir(){
  if [ ! -d "appgalleryResult" ];then
    mkdir appgalleryResult
  else
    echo "文件夹已经存在"
  fi
}

printf "file_path = ${file_path} & huawei_filename = ${huawei_filename} & file_suffix = ${file_suffix}\n"
mkResultDir
getToken
getAppInfo
updateNewFeatures
getFileUploadUrl
uploadFile
updateAppFileInfo
submitApp