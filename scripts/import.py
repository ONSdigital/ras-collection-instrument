#!/usr/bin/python3
#
#   This is an import routine to setup some specific data for the guys in Titchfied
#
import xlsxwriter
import requests
import sys
import os
#
COLLECTION_EXERCISE = '14fb3e68-4dca-46db-bf49-04b84e07e77c'
API_UPLOAD = '{}/collection-instrument-api/1.0.2/upload/{}/{}'
TYPE = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'

urls = {
    'dev': 'http://api-dev.apps.mvp.onsclofo.uk',
    'local': 'http://localhost:8080'
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

        fname = ru_ref+'.xlsx'
        workbook = xlsxwriter.Workbook(fname)
        worksheet = workbook.add_worksheet()
        worksheet.set_column('A:A', 25)
        worksheet.write('A1', 'RU_REF = {}'.format(ru_ref))
        workbook.close()

        files = {'files[]': (fname, open(fname, 'rb'), TYPE, {'Expires': 0})}
        url = API_UPLOAD.format(HOST, COLLECTION_EXERCISE, fname)
        r = requests.post(url, files=files)
        if r.status_code != 200:
            print('%% upload error "{}" - "{}"'.format(r.status_code, r.text))
            exit(1)
        print(".", end='')
        sys.stdout.flush()
        os.remove(fname)
