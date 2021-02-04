#!/usr/bin/python

# To create a dictionary table
# with de budgetary structure
# for different fiscal years

import os
import re
import zipfile
import requests
import sqlite3
import pandas as pd


# Glabal parameters
# URL must be updated
URL = 'http://www.transparenciafiscal.gob.sv/downloads/zip/700-DINAFI-CT-2020-2002.zip'
ZIPFILE = 'structure.zip'
DB = 'master.db'

# Downloading data from the web
content = requests.get(URL).content
with open(ZIPFILE, 'wb') as fd:
    fd.write(content)

# Loading data into a dataframe
data = pd.read_csv(
    ZIPFILE,
    sep=';',
    skiprows=1,
    compression='zip',
    converters={
        'INSTITUCION': str,
        'UNIDAD_PRES': str,
        'BD_UNIDAD_PRES': str,
        'LINEA_TRABAJO': str,
        'BD_LINEA_TRABAJO': str,
    }
)

# Adjusting column names
data.rename(
        columns={
            'EJERCICIO': 'year',
            'INSTITUCION': 'office',
            'UNIDAD_PRES': 'unit',
            'BD_UNIDAD_PRES': 'unit_name',
            'LINEA_TRABAJO': 'line',
            'BD_LINEA_TRABAJO': 'line_name'
        },
        inplace=True
    )

# Filling codes with left zeros
data['office'] = data.office.apply(lambda s: s.zfill(4))
data['unit'] = data.unit.apply(lambda s: s.zfill(2))
data['line'] = data.line.apply(lambda s: s.zfill(4))

# Removing codes in names
def remove_codes(s):
    if s:
        p = re.compile('^\d+\s+')
        m = p.match(s)
        if m:
            return s.replace(m.group(), '')
    return s

data['unit_name'] = data.unit_name.apply(remove_codes)
data['line_name'] = data.line_name.apply(remove_codes)

conn = sqlite3.connect(DB)

# Table for units
unit = data[['year', 'office', 'unit', 'unit_name']].copy()
unit.rename(columns={
    'unit': 'program', 
    'unit_name': 'program_name'
}, inplace=True)
unit.set_index(['year', 'office', 'program'], inplace=True)
unit.to_sql('program', conn, if_exists='replace')

# Table for lines
line = data[['year', 'office', 'line', 'line_name']].copy()
line.rename(columns={
    'line': 'program', 
    'line_name': 'program_name'
}, inplace=True)
line.set_index(['year', 'office', 'program'], inplace=True)
line.to_sql('program', conn, if_exists='append')
conn.close()

# Clean up
os.remove(ZIPFILE)
