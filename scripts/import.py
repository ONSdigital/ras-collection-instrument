#!/usr/bin/python3
#
#   This is an import routine to setup some specific data for the guys in Titchfied
#
import os
import sys

import requests
import xlsxwriter


COLLECTION_EXERCISE = '14fb3e68-4dca-46db-bf49-04b84e07e77c'
# COLLECTION_EXERCISE = 'c6467711-21eb-4e78-804c-1db8392f93fb'
# COLLECTION_EXERCISE = "c6467711-21eb-4e78-804c-1db8392f93bb"
# COLLECTION_EXERCISE = "c6467711-21eb-4e78-804c-1db8392f93aa"
API_UPLOAD = '{}/collection-instrument-api/1.0.2/upload/{}/{}'
TYPE = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
urls = {
    'dev': 'http://api-dev.apps.devtest.onsclofo.uk',
    'local': 'http://localhost:8002',
    'test': 'http://ras-collection-instrument-test.apps.devtest.onsclofo.uk',
    'int': 'http://ras-collection-instrument-int.apps.devtest.onsclofo.uk',
    'demo': 'http://ras-collection-instrument-demo.apps.devtest.onsclofo.uk',
    'sit': 'http://ras-collection-instrument-sit.apps.devtest.onsclofo.uk',
    'ci': 'http://ras-collection-instrument-ci.apps.devtest.onsclofo.uk'
}

if len(sys.argv) < 2 or sys.argv[1] not in urls:
    print("Please specify an environment from;")
    print(urls.keys())
    sys.exit(1)

HOST = urls[sys.argv[1]]

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

        url = API_UPLOAD.format(HOST, COLLECTION_EXERCISE, fname)
        basic_auth = (os.getenv('SECURITY_USER_NAME'), os.getenv('SECURITY_USER_PASSWORD'))
        files = {'files[]': (fname, open(fname, 'rb'), TYPE, {'Expires': 0})}
        r = requests.post(url, auth=basic_auth, files=files, verify=False)

        if r.status_code != 200:
            print('%% upload error "{}" - "{}"'.format(r.status_code, r.text))
            exit(1)
        print(".", end='')
        sys.stdout.flush()
        os.remove(fname)

