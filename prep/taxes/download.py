# Data is downloaded from Portal de Transparencia Fiscal
#
# 2020 Mar.
# Fundación Nacional para el Desarrollo
# Centro de Monitoreo e Incidencia Fiscal
#
# Contributors:
#   - Jaime Lopez <jailop AT protonmail DOT com>

import os
import zipfile
import requests


URL = "http://www.transparenciafiscal.gob.sv/downloads/zip/0700-DGII-DA-{}-IMP.zip"

for year in range(2010, 2020):
	filename = f"tmp/taxes{year}.zip"
	if not os.path.exists(filename):
		try:
			content = requests.get(URL.format(year)).content

			with open(filename, 'wb') as fd:
				fd.write(content)
				print(filename)
		except:
			print('Error: %s cannot be downloaded' % filename)

for year in range(2010, 2020):
	filename = f"tmp/taxes{year}.zip"
	with zipfile.ZipFile(filename, 'r') as zip:
		zip.extractall('./tmp')
		print(filename)
