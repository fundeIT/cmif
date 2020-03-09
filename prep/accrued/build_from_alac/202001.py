import os
import sqlite3
import pandas as pd
from dotenv import load_dotenv

# Setting environment
load_dotenv()

URL = 'https://alac.funde.org/docs/5e62954cd6fa0f2730db97eb'

data = pd.read_excel(URL,
    converters={
        'INSTITUCION': str,
        'UNIDAD PRESUP': str,
        'LINEA DE TRABAJO': str,
        'FUENTE_FINANC': str,
        'CLASIF_PRESUP': str
    }
)
data.rename(columns={
    'EJERCICIO': 'year',
    'INSTITUCION': 'office',
    'UNIDAD PRESUP': 'unit',
    'LINEA DE TRABAJO': 'line',
    'FUENTE_FINANC': 'source',
    'CLASIF_PRESUP': 'object',
    'APROBADO': 'approved',
    'MODIFICADO': 'modified',
    'COMPROMETIDO': 'reserved',
    'DEVENGADO': 'accrued'
    }, inplace=True
)
data['month'] = 1
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
