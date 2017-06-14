#!/usr/bin/env python3

from os import getenv
from sys import argv, stdout
import requests

def usage():
    print('Usage: {} [live|local] (id) (count)'.format(argv[0]))
    exit(1)

if len(argv) < 4:
    usage()

host = argv[1]
if host not in ['local', 'live', 'dev']:
    print('%% expecting either "local" or "live" for host')
    exit(1)

if host == 'local':
    host = 'http://localhost:8080'
elif host == 'live':
    host = 'http://ras-collection-instrument-demo.apps.mvp.onsclofo.uk'
else: 
    host = 'http://ras-collection-instrument-dev.apps.mvp.onsclofo.uk'

ref = argv[2]
count = int(argv[3])

API_UPLOAD = getenv('API_UPLOAD', '{}/collection-instrument-api/1.0.3/upload/{}/upload.txt'.format(host, ref))

actual = 0
for i in range(0, count):
    files = {'files[]': ('upload.txt', open('upload.txt', 'rb'), 'text/html', {'Expires': 0})}
    r = requests.post(API_UPLOAD, files=files)
    if r.status_code != 200:
        print('%% upload error "{}" - "{}"'.format(r.status_code, r.text))
        exit(1)
    print(".", end='')
    stdout.flush()

print(r.text)
