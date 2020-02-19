# From previously downloaded Excel files
# the accrued budget database is build
#
# 2020 Feb.
# Fundación Nacional para el Desarrollo
# Centro de Monitoreo e Incidencia Fiscal
#
# Contributors:
#   - Jaime Lopez <jailop AT protonmail DOT com>

import os
import pandas as pd

def excel2csv():
    # Getting names of Excel files
    # in the current directory
    filenames = [
        filename
            for filename in os.listdir('.')
                if filename[-4:] == 'xlsx'
    ]

    # Loading Excel files in Pandas dataframes
    dfs = [
        pd.read_excel(
            filename,
            converters={
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
        for filename in filenames
    ]

    # Removing invalid rows
    #
    # To determine which rows are invalid a visual
    # inspection was made over the datastes
    # The invalid rows are the last three in which
    # a message was annotated by the data provider
    for df in dfs:
        df.drop(df[-3:].index, inplace=True)

    # Adjusting column names before joining
    dfs[0].rename(columns={'AREA_GESTIO': 'AREA_GESTION'}, inplace=True)

    # Joining datasets in a big one
    df = pd.concat(dfs)

    # Filling with zeros office code
    df['INSTITUCION'] = df['INSTITUCION'].apply(lambda s: s.zfill(4))

    # Saving data in a CSV file
    df.to_csv('accrued.csv', index=False)

if __name__ == '__main__':
    excel2csv()
