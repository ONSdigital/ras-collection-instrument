#!/usr/bin/python3
#
#   This is an import routine to setup some specific data for the guys in Titchfied
#
import os
import sys

import requests
import xlsxwriter


API_UPLOAD = '{}/collection-instrument-api/1.0.2/upload/{}/{}'
TYPE = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
COLLECTION_EXERCISE_ID = os.getenv('COLLECTION_EXERCISE_ID')
HOST = os.getenv('COLLECTION_INSTRUMENT_HOST')

if not HOST:
    print("Please specify the collection instrument host with environment variable; 'COLLECTION_INSTRUMENT_HOST'")
    sys.exit(1)
if not COLLECTION_EXERCISE_ID:
    print("Please specify the collection exercise id with environment variable; 'COLLECTION_EXERCISE_ID'")
    sys.exit(1)


with open('ru_ref_import.txt') as io:
    while True:
        ref = io.readline()
        if not ref:
            break
        parts = ref.split('"')
        if len(parts) < 2:
            continue
        ru_ref = parts[1]

        fname = '{}.xlsx'.format(ru_ref)
        workbook = xlsxwriter.Workbook(fname)
        worksheet = workbook.add_worksheet()
        worksheet.set_column('A:A', 25)
        worksheet.write('A1', 'RU_REF = {}'.format(ru_ref))
        workbook.close()

        url = API_UPLOAD.format(HOST, COLLECTION_EXERCISE_ID, fname)
        basic_auth = (os.getenv('SECURITY_USER_NAME'), os.getenv('SECURITY_USER_PASSWORD'))
        files = {'files[]': (fname, open(fname, 'rb'), TYPE, {'Expires': 0})}
        r = requests.post(url, auth=basic_auth, files=files, verify=False)

        if r.status_code != 200:
            print('%% upload error "{}" - "{}"'.format(r.status_code, r.text))
            exit(1)
        print(".", end='')
        sys.stdout.flush()
        os.remove(fname)

