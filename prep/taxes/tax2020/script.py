#!/usr/bin/python

# Actualización de datos de impuestos 2020
#
# El propósito de este script es actualizar la base de datos de CEMIF con los
# datos de impuestos correspondientes al ejercicio fiscal 2020. Los datos se
# encuentran publicados en el Transparencia Fiscal del Ministerio de Hacienda.

import requests
from zipfile import ZipFile
import pandas as pd
import sqlite3

def download():
    """
    El propósito de esta función es descargar los datos del Portal de
    Transparencia Fiscal del Ministerio de Hacienda. Los datos están publicados
    en formato zip, por lo cual, los datos son descargados y a continuación
    guardados respetando el formato.
    """
    url = "https://www.transparenciafiscal.gob.sv/downloads/zip/0700-DGII-DA-2020-IMP02.zip"
    zipname = "taxes2020.zip"
    content = requests.get(url).content
    with open(zipname, "w") as fd:
        fd.write(content)
    with ZipFile(zipname, 'r') as fz:
        fz.extractall()

def normalize():
    """
    En esta función los datos son normalizados. Eso significa que los nombres de
    las columnas son adecuados, conforme el esquema de la base de datos, y se
    hacen algunos ajustes de formato en los datos, por ejemplo en los códigos de
    departamentos y municipios. A continuación se depura la lista de columnas
    admitidas y se crea un índice. El dataset modificado es devuelto como
    resultado de la functión.
    """
    data = pd.read_csv('Ingresos-2020.csv', sep=';')
    data.columns
    data = data.rename(columns={
        'ANIO': 'year',
        'MES': 'month',
        'CLASE': 'subject',
        'DEPARTAMENTO': 'department',
        'MUNICIPIO': 'municipality',
        'ACTECO': 'activity',
        'CODIMP': 'tax',
        'VALOR': 'amount'
        })
    data['department'] = data['department'].apply(lambda s: str(s).zfill(2))
    data['municipality'] = data['municipality'].apply(lambda s: str(s).zfill(4))
    fields = [
        'year', 'month', 'subject',
        'department', 'municipality',
        'activity', 'tax', 'amount'
    ]
    data = data[fields]
    data.set_index(fields[:-1], inplace=True, verify_integrity=False)
    return data

def updatedb(data):
    """
    Esta función se encarga de actualizar la base de datos. Recibe los datos
    normalizados, elimina de la base de datos todo registro que corresponda al
    año 2020 y a continuación, cargo los datos normalizados en la base de datos.
    """
    conn = sqlite3.connect('../../master.db')
    cur = conn.cursor()
    cur.execute('DELETE FROM tax WHERE year=2020')
    conn.commit()

    data.to_sql('tax', conn, if_exists='append', index=True)

if __name__ == '__main__':
    data = normalize()
    updatedb(data)
