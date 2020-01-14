import os
import sys
import glob
import requests
import zipfile
from dotenv import load_dotenv
import pandas as pd
import sqlite3

load_dotenv()

def tableExists(tableName, conn=None):
    if conn == None:
        conn = sqlite3.connect(os.getenv('DBNAME'))
    c = conn.cursor()
    c.execute("SELECT count(name) FROM sqlite_master WHERE type='table' AND name='{}'".format(tableName))
    if c.fetchone()[0] == 1:
        flag = True
    else:
        flag = False
    conn.close()
    return flag

def downloadDatasets(verbose=False):
    success = True
    years = range(int(os.getenv('START_YEAR')), int(os.getenv('END_YEAR')))
    url = 'http://www.transparenciafiscal.gob.sv/downloads/zip/700-DINAFI-DA-{}-CPG.zip'
    for y in years:
        address = url.format(y)
        pos = url.rfind('/') + 1
        filename = address[pos:]
        if os.path.exists(filename):
            if verbose:
                print('File {} has been already downloaded.'.format(filename))
            continue
        try:
            if verbose:
                sys.stdout.write('Getting {} ... '.format(filename))
            resource = requests.get(address)
            with open(filename, 'wb') as fd:
                fd.write(resource.content)
            if verbose:
                sys.stdout.write('unzipping ... ')
            with zipfile.ZipFile(filename, 'r') as fz:
                fz.extractall('.')
            if verbose:
                sys.stdout.write(' done.\n')
        except:
            success = success and False
    return success

def extractData(filename):
    data = pd.read_csv(filename, sep=';')
    data.rename(columns={
        'EJERCICIO': 'year', 
        'MES': 'month', 
        'TIPO_INSTITUCION': 'level', 
        'BD_TIPO_INSTITUCION': 'level_name',
        'INSTITUCION': 'office', 
        'BD_INSTITUCION': 'office_name', 
        'UNIDAD_PRES': 'unit', 
        'BD_UNIDAD_PRES': 'unit_name',
        'LINEA_TRABAJO': 'line', 
        'BD_LINEA_TRABAJO': 'line_name', 
        'AREA_GESTION': 'area', 
        'BD_AREA_GESTION': 'area_name',
        'FUENTE_FINANC': 'source', 
        'BD_FTE_FINANCIAMIENTO': 'source_name', 
        'FUENTE_RECURS': 'financier',
        'BD_FTE_RECURSOS': 'financier_name', 
        'RUBRO': 'heading', 
        'DESCRIPCION_DE_RUBRO': 'heading_name', 
        'CUENTA': 'subheading',
        'DESCRIPCION_DE_CUENTA': 'subheading_name', 
        'PROGRAMADO': 'approved', 
        'MODIFICACION': 'shifted',
        'PROGRAMADO_MODIFICADO': 'modified', 
        'COMPROMISO': 'reserved', 
        'DEVENGADO': 'accrued'
        }, inplace=True)
    data['object'] = data['subheading']
    df = data[[
        'year', 'month', 'office', 'unit', 
            'line', 'area', 'source', 'financier', 'object', 
            'approved', 'shifted', 'modified', 'accrued',
        ]]
    conn = sqlite3.connect(os.getenv('DBNAME'))
    df.set_index([ 
            'year', 'month', 'office', 'unit',
            'line', 'area', 'source', 'financier', 'object'
        ])
    df.to_sql('accrued', conn, if_exists='append', index=True)
    conn.close()
    return data, df
    
def processFiles(path='.'):
    csvFiles = glob.glob(path + '/*.csv')
    os.remove('accrued.db')
    for ds in csvFiles:
        data, df = extractData(ds)
    conn = sqlite3.connect(os.getenv('DBNAME'))
    office = data[['office', 'office_name', 'level']].drop_duplicates()
    office.set_index('office', inplace=True)
    office.to_sql('office', conn)
    level = data[['level', 'level_name']].drop_duplicates()
    level.set_index('level', inplace=True)
    level.to_sql('level', conn)
    area = data[['area', 'area_name']].drop_duplicates()
    area.set_index('area', inplace=True)
    area.to_sql('area', conn)
    source = data[['source', 'source_name']].drop_duplicates()
    source.set_index('source', inplace=True)
    source.to_sql('source', conn)
    financier = data[['financier', 'financier_name']].drop_duplicates()
    financier.set_index('financier', inplace=True)
    financier.to_sql('financier', conn)
    conn.close()


if __name__ == '__main__':
    downloadDatasets()
    processFiles()
