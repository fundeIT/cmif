# Prepare the taxes db

import os
import sqlite3
import pandas as pd

# Global variables
SOURCES = 'taxes/sources/'
DB = 'master.db'

def make_taxes_table():
    # Loading data from sources
    #   Data is provided by Ministerio de Hacienda
    #   Currently, csv files use `;` as separator
    data = pd.concat([
        pd.read_csv(SOURCES + filename, sep=';') 
        for filename in os.listdir(SOURCES) if filename.find('.csv') > 0
    ], sort=False)

    # Data transformation
    #  Column names are standarized
    data.rename(columns={
        'ANIO': 'year',
        'MES': 'month',
        'CLASE': 'subject',
        'ZONA': 'region',
        'DEPARTAMENTO': 'department',
        'MUNICIPIO': 'municipality',
        'IMPORTANCIA': 'relevance', 
        'ACTECO': 'activity', 
        'CODIMP': 'tax',
        'VALOR': 'amount'
    }, inplace=True)
    #  Department and municipality code are filled with zeros on the left
    data['department'] = data['department'].apply(lambda s: str(s).zfill(2))
    data['municipality'] = data['municipality'].apply(lambda s: str(s).zfill(4))
    data.set_index([
        'year', 'month', 'subject', 
        'department', 'municipality',
        'activity', 'tax'
    ], inplace=True)

    # Transfering data to the DB
    conn = sqlite3.connect(DB)
    data.to_sql('tax', conn, if_exists='replace', index=True)
    conn.close()

def make_taxes_reference_tables():
    conn = sqlite3.connect(DB)
    
    taxes_class = pd.read_csv('taxes/refs/impuesto.csv', sep=';')
    taxes_class.rename(columns={
        'CODIGO': 'tax',
        'NOMBRE': 'tax_name'
    }, inplace=True)
    taxes_class.to_sql('tax_class', conn, if_exists='replace', index=False)

    activities = pd.read_csv('taxes/refs/actividad-economica.csv', sep=';')
    activities.rename(columns={
        'CODIGO': 'activity',
        'NOMBRE': 'activity_name'
    }, inplace=True)
    activities.to_sql('activity', conn, if_exists='replace', index=False)

if __name__ == '__main__':
    make_taxes_table()
    make_taxes_reference_tables()
