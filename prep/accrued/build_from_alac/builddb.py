# From previously downloaded Excel files
# the accrued budget database is build
#
# 2020 Feb.
# Fundación Nacional para el Desarrollo
# Centro de Monitoreo e Incidencia Fiscal
#
# Contributors:
#   - Jaime Lopez <jailop AT protonmail DOT com>

# Loading libraries
import os
import sqlite3
import pandas as pd
from dotenv import load_dotenv

# Setting environment
load_dotenv()

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
    df.to_sql(fields[table_name_index], conn, if_exists='replace')
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

def buildDB():
    """
    This is the main function that builds the database
    It reads the CSV file produced by excel2csv
    and make the DB tables in accrued.db
    """
    data = pd.read_csv(
        'accrued.csv',
        dtype={
            'MES': int,
            'INSTITUCION': str,
            'UNIDAD PRESUP': str,
            'LENEA TRABAJO': str,
            'AREA_GESTIO': str,
            'AREA_GESTION': str,
            'FUENTE_FINANC': str,
            'FUENTE_RECURS': str,
            'RUBRO': str,
            'CUENTA': str,
            'ESPECIFICO': str
        }
    )
    data.rename(columns={
        'EJERCICIO': 'year',
        'MES': 'month',
        'INSTITUCION': 'office',
        'NOMBRE': 'office_name',
        'UNIDAD PRESUP': 'unit',
        'NOMBRE.1': 'unit_name',
        'LENEA TRABAJO': 'line',
        'NOMOBRE': 'line_name',
        'AREA_GESTION': 'area',
        'NOMBRE.2': 'area_name',
        'FUENTE_FINANC': 'source',
        'NOMBRE.3': 'source_name',
        'FUENTE_RECURS': 'financier',
        'NOMBRE.4': 'financier_name',
        'RUBRO': 'heading',
        'NOMBRE.5': 'heading_name',
        'CUENTA': 'subheading',
        'NOMBRE.6': 'subheading_name',
        'ESPECIFICO': 'object',
        'MOMBRE': 'object_name',
        'PRORAMADO': 'approved',
        'MODIFICACIONES': 'shifted',
        'MODIFICADO': 'modified',
        'COMPROMETIDO': 'reserved',
        'MONTO_DEVENG': 'accrued'
        }, inplace=True
    )
    data['level'] = data['office'].apply(
        lambda s: 1 if (int(s) // 100 * 100) == int(s) else 2
    )
    data['level_name'] = data['level'].apply(
        lambda i: 'Gobierno central' if i == 1 else 'Descentralizadas'
    )
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
    df.to_sql('accrued', conn, if_exists='replace', index=True)
    conn.close()
    createDictionaries(data)

if __name__ == '__main__':
    buildDB()
