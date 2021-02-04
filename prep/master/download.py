#!/usr/bin/python

# Purpose:
# This script downloads budget datasheets from ALAC's website. Those datasheets
# has been obtained by information requests made to Ministerio de Hacienda.
# Links are stored in 'sources.txt'. Downloaded files are saved in the folder
# 'src'.
#
# Usage:
#     $ ./download.py
#
# (2020) FUNDE-CEMIF

import os
import requests

SOURCES_FILE = 'defs/sources.txt'
URL_BASE = 'https://alac.funde.org'
DIR_TARGET = 'src/'

def downloadFile(url, filename):
    print(filename + '... ', end='', flush=True)
    try:
        # Ok. So, download and saved it.
        req = requests.get(url)
        if req.ok:
            with open(filename, 'wb') as fout:
                fout.write(req.content)
        print('OK')
    except:
        # Maybe time response is exceeded
        print('binFailed')

if __name__ == "__main__":
    fin = open(SOURCES_FILE, 'r')
    while True:
        line = fin.readline()
        if not line:
            # The end of the file has been reached
            break
        line = line.strip()
        if line == '' or line[0] == '#':
            # The line is empty or is a comment
            continue
        if line.find(URL_BASE) >= 0:
            url, filename = line.split()
            filename = DIR_TARGET + filename + '.xlsx'
            if os.path.exists(filename):
                # File has been already downloaded
                continue
            downloadFile(url, filename)
    fin.close()
