# Data is downloaded from ALAC website.
# Information was obtained by LAIP requests.
#
# 2020 Feb.
# Fundación Nacional para el Desarrollo
# Centro de Monitoreo e Incidencia Fiscal
#
# Contributors:
#   - Jaime Lopez <jailop AT protonmail DOT com>

import sys
import requests

URLs = [
    'http://alac.funde.org/docs/5e45856f0634d8e44d8b41a0',
    'http://alac.funde.org/docs/5e4586230634d8e44d8b41b5',
]

def download():
    for url in URLs:
        try:
            page = requests.get(url)
        except:
            print('Download failed')
            print('url: {}'.format(url))
            print('Execution is aborted')
            sys.exit(1)
        # The filename starts after the last /
        pos = url.rfind('/') + 1
        # Downloaded files are in Excel format
        filename = url[pos:] + '.xlsx'
        with open(filename, 'wb') as fd:
            fd.write(page.content)

if __name__ == '__main__':
    download()
