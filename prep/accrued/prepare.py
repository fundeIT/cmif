#!/usr/bin/env python
#
# Prepare the accrued database
#
# This script download the accrued datasets from
# Portal de Transparencia Fiscal and build a
# database with them.
#
# (2020) Fundación Nacional para el Desarrollo
#
# Contributors:
#   Jaime Lopez <jailop AT gmail DOT com>

import os
import sys
import glob
import requests
import zipfile
from dotenv import load_dotenv
import pandas as pd
import sqlite3
import multiprocessing as mp

load_dotenv()

def tableExists(tableName, conn=None):
    """
    It checks if a table exists in a SQLite database.
    
    Params:
        tableName: the name of the table to be checked
        conn: SQLite database connection
    
    Return:
        True is table exists, False otherwise
    """
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

def downloadFile(year):
    """
    It downloads a file from the web. An URL address template must be given
    in the env file. The URL will formed merging the year. The dataset
    downloaded is saved as a file.
    
    Params:
        year : Year of the dataset to be downloaded
    
    Return:
        True is success, False otherwise
    """
    flag = True
    address = os.getenv('URL').format(year)
    pos = address.rfind('/') + 1
    filename = address[pos:]
    if not os.path.exists(filename):
        try:
            resource = requests.get(address)
            with open(filename, 'wb') as fd:
                fd.write(resource.content)
            with zipfile.ZipFile(filename, 'r') as fz:
                fz.extractall('.')
        except:
            flag = False
    return flag

def downloadDatasets():
    """
    It downloads the datasets for the period given in the env file.
    START_YEAR and END_YEAR must be defined.
    
    Return:
        True if successing downloading all datasets, False otherwise
    """
    years = range(int(os.getenv('START_YEAR')), int(os.getenv('END_YEAR')))
    with mp.Pool(mp.cpu_count()) as p:
        ret = p.map(downloadFile, years)    
    flag = True
    for r in ret:
        flag &= r
    return flag

def extractData(filename):
    """
    It extract key data from the downloaded datasets and build
    the 'accrued' table in the database.

    Return:
        The dataset in mid processed
    """
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
    return data
   
def buildDict(data, fields, upper_index, table_name_index):
    """
    It builds a dictionary for data lookup.

    Params:
        data : Dataframe containing the data
        fields: List of fields to be included in the dictionary
        upper_index: Index of the upper bond field for index
        table_name_index: Index of the field which will be used
                          to name the dictionary
    """
    df = data[fields].drop_duplicates()
    df.set_index(fields[:upper_index], inplace=True)
    conn = sqlite3.connect(os.getenv('DBNAME'))
    df.to_sql(fields[table_name_index], conn)
    conn.close()

def createDictionaries(data):
    """
    It builds all dictionaries from the dataset

    Params:
        data: Dataframe containing the data
    """
    buildDict(data, ['office', 'office_name', 'level'], 1, 0)
    buildDict(data, ['level', 'level_name'], 1, 0)
    buildDict(data, ['area', 'area_name'], 1, 0)
    buildDict(data, ['source', 'source_name'], 1, 0)
    buildDict(data, ['financier', 'financier_name'], 1, 0)
    buildDict(data, ['year', 'office', 'unit', 'unit_name'], 3, 2)
    buildDict(data, ['year', 'office', 'unit', 'line', 'line_name'], 4, 3)

def processFiles(path='.'):
    """
    It convert CSV files to a SQL database

    Params:
        path : Optional path where CSV files are located
    """
    csvFiles = glob.glob(path + '/*.csv')
    try:
        os.remove('accrued.db')
    except:
        print(OSError.strerror)
    with mp.Pool(mp.cpu_count()) as p:
        ret = p.map(extractData, csvFiles)    
    data = pd.concat(ret, sort=False)
    createDictionaries(data)

def cleanWorkSpace():
    """
    It cleans the work space deleting the zip and csv files.
    """
    for fileName in glob.glob('*.zip') + glob.glob('*.csv'):
        os.remove(fileName)

if __name__ == '__main__':
    downloadDatasets()
    processFiles()
    cleanWorkSpace()
