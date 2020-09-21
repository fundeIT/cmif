import os
import sqlite3
import pandas as pd
from dotenv import load_dotenv

# Setting environment
load_dotenv()

URL = 'ejecucion_202004-06.xlsx'

data = pd.read_excel(URL,
    converters={
        'INSTITUCION': str,
        'SUBSTR(ESTRUC_PRESUP,1,2)': str,
        'ESTRUC_PRESUP': str,
        'FUENTE_FINANC': str,
        'CLASIF_PRESUP': str
    }
)
data.rename(columns={
    'EJERCICIO': 'year',
    'INSTITUCION': 'office',
    'SUBSTR(ESTRUC_PRESUP,1,2)': 'unit',
    'ESTRUC_PRESUP': 'line',
    'FUENTE_FINANC': 'source',
    'CLASIF_PRESUP': 'object',
    'MES': 'month',
    'MODIFICADO': 'approved',
    'MONTO_AUTORI': 'modified',
    'MONTO_DEVENG': 'accrued'
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
