import os
import sqlite3
import pandas as pd
from dotenv import load_dotenv

# Setting environment
load_dotenv()

URL = 'https://alac.funde.org/docs/5f2da3adbb58b73471a3e929'

data = pd.read_excel(URL,
    converters={
        'INSTITUCION': str,
        'UNIDAD PRES': str,
        'LINE DE TRABAJO': str,
        'FUENTE_FINANC': str,
        'ESPECIFICO': str
    }
)
data.rename(columns={
    'EJERCICIO': 'year',
    'INSTITUCION': 'office',
    'UNIDAD PRES': 'unit',
    'LINE DE TRABAJO': 'line',
    'FUENTE_FINANC': 'source',
    'ESPECIFICO': 'object',
    'MES': 'month',
    'VOTADO': 'approved',
    'MODIFICADO': 'modified',
    'COMPROMETIDO': 'reserved',
    'DEVENGADO': 'accrued'
    }, inplace=True
)
data['area'] = ''
data['financier'] = ''
data['office'] = data['office'].apply(lambda s: s.zfill(4))
data['shifted'] = data['modified'] - data['approved']
df = data[[
    'year', 'month', 'office', 'unit',
    'line', 'area', 'source', 'financier', 'object',
    'approved', 'shifted', 'modified', 'accrued',
]]
df.set_index([
    'year', 'month', 'office', 'unit',
    'line', 'area', 'source', 'financier', 'object'
], inplace=True)
conn = sqlite3.connect(os.getenv('DBNAME'))
df.to_sql('accrued', conn, if_exists='append', index=True)
conn.close()
