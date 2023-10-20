#!/usr/bin/python
#
# Copyright 2014 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the 'License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""AAB upload script to be used with service account."""

import argparse
import json
import os

import httplib2
from oauth2client.service_account import ServiceAccountCredentials
from googleapiclient.discovery import build
from oauth2client import client
import glob

import utils

TRACK = 'production'  # Can be 'alpha', beta', 'production' or 'rollout'

# Declare command-line flags.
argparser = argparse.ArgumentParser(add_help=False)
argparser.add_argument('package_name',
                       nargs='?',
                       default=json.load(open("config.json", 'r'))["packageName"],
                       help='The package name. Example: com.android.sample')
argparser.add_argument('apk_file',
                       nargs='?',
                       default='app-longbridge-online-google.aab',
                       help='The path to the APK file to upload.')


def main():
    # Authenticate and construct service.
    SCOPES = ['https://www.googleapis.com/auth/androidpublisher']
    SERVICE_ACCOUNT_FILE = 'service_account.json'

    credentials = ServiceAccountCredentials.from_json_keyfile_name(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    http = httplib2.Http()
    http = credentials.authorize(http)
    service = build('androidpublisher', 'v3', http=http)

    # Process flags and read their values.
    flags = argparser.parse_args()
    package_name = flags.package_name
    apk_file = flags.apk_file

    try:
        edit_request = service.edits().insert(body={}, packageName=package_name)
        result = edit_request.execute()
        edit_id = result['id']

        apk_response = service.edits().bundles().upload(
            editId=edit_id,
            packageName=package_name,
            media_body=apk_file,
            media_mime_type="application/octet-stream").execute()

        print('Version code %d has been uploaded' % apk_response['versionCode'])

        track_response = service.edits().tracks().update(
            editId=edit_id,
            track=TRACK,
            packageName=package_name,
            body={u'releases': [{
                u'versionCodes': [str(apk_response['versionCode'])],
                u'status': u'completed',
                u'releaseNotes': getReleaseNote()
            }]}).execute()

        print('Track %s is set with releases: %s' % (
            track_response['track'], str(track_response['releases'])))

        commit_request = service.edits().commit(
            editId=edit_id, packageName=package_name).execute()

        print('Edit "%s" has been committed' % (commit_request['id']))

    except client.AccessTokenRefreshError:
        print('The credentials have been revoked or expired, please re-run the '
              'application to re-authorize')


def getReleaseNote():
    new_release_notes = []
    for release_note_file in glob.glob('release-note-*.txt'):
        release_note = utils.readFile(release_note_file)
        if len(release_note) != 0:
            filename_without_ext, file_extension = os.path.splitext(os.path.basename(release_note_file))
            new_release_notes.append(
                {'language': filename_without_ext.replace("release-note-", ""), 'text': release_note})
    return new_release_notes


if __name__ == '__main__':
    main()
