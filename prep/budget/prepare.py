#!/usr/bin/env python

import sqlite3
import pandas as pd
import sys

DBNAME = 'budget.db'

moments = {
    'Preliminary': 1,
    'Proposed': 2,
    'Aproved': 3,
    'Modified': 4,
    'Accrued': 5
}

def num_to_code(col, zeros=0):
    col_zfill = lambda value: value.zfill(zeros)
    ret = col.apply(int).apply(str).apply(col_zfill)
    return ret

def set_as_codes(data, cols):
    for col in cols.keys():
        data[col] = num_to_code(data[col], cols[col])

def get_classificator():
    source = 'sources/ClasificadorPresupuestario.csv'
    data = pd.read_csv(source, sep=';')
    data.columns = ['object', 'object_name']
    data['object'] = data['object'].astype(str)
    data['object_name'] = data.object_name.apply(str.strip)
    data.set_index('object', inplace=True)
    conn = sqlite3.connect(DBNAME)
    data.to_sql('object', conn, if_exists='replace')
    conn.close()
    return data

def get_structure():
    source = 'sources/Estructura-Presupuestaria-2007-2019.csv'
    data = pd.read_csv(source, sep=';', skiprows=1)
    data.rename(
        columns={
            'EJERCICIO': 'year',
            'INSTITUCION': 'office',
            'UNIDAD_PRES': 'unit',
            'BD_UNIDAD_PRES': 'unit_name',
            'LINEA_TRABAJO': 'line',
            'BD_LINEA_TRABAJO':
            'line_name'},
        inplace=True
    )
    data['line'] = data.line.apply(lambda s: s.replace('NA', ''))
    data = data[data.line.apply(len) >= 3]
    data['line'] = data.line.apply(lambda s: s[-2:])
    data['unit'] = num_to_code(data['unit'], 2)
    data['office'] = num_to_code(data['office'], 4)
    conn = sqlite3.connect(DBNAME)
    unit = data[['year', 'office', 'unit', 'unit_name']]
    unit.set_index(['year', 'office', 'unit'], inplace=True)
    unit.to_sql('unit', conn, if_exists='replace')
    line = data[['year', 'office', 'unit', 'line', 'line_name']]
    line.set_index(['year', 'office', 'unit', 'line'], inplace=True)
    line.to_sql('line', conn, if_exists='replace')
    conn.close()
    return data

def get_budget_2012_2017():
    data = pd.read_excel('sources/ejecucion_2012-2017.xlsx', skiprows=7)
    data.rename(
        columns={
            'Año': 'year',
            'Código Institución': 'office',
            'Institución': 'office_name',
            'Código Objeto Presupuestario': 'object',
            'Objeto Presupuestario': 'object_name',
            'Monto programado o votado': 'approved',
            'Presupuesto Modificado': 'modified',
            'Monto Devengado': 'accrued',
        },
        inplace=True
    )
    source = 'Código y Nombre Fuente Financiamiento'
    data['source'] = data[source].apply(lambda s: s[0:1])
    data['source_name'] = data[source].apply(lambda s: s[2:])
    del data[source]
    line = 'Linea Trabajo'
    data['unit'] = data[line].apply(lambda s: s[0:2])
    data['line'] = data[line].apply(lambda s: s[2:4])
    data['line_name'] = data[line].apply(lambda s: s[5:])
    del data[line]
    set_as_codes(data, {
        'office': 4,
        'source': 1,
        'unit': 2,
        'line': 2,
        'object': 5
    })
    data['level'] = data['office'].apply(lambda s: 'CG' if s[-2:] == '00' else 'DE')
    conn = sqlite3.connect(DBNAME)
    offices = data[['office', 'office_name', 'level']].drop_duplicates()
    offices.set_index('office', inplace=True)
    offices.to_sql('office', conn, if_exists='replace')
    del data['office_name']
    del data['level']
    # lines = data[['year', 'office', 'unit', 'line', 'line_name']].drop_duplicates()
    # lines.set_index(['year', 'office', 'unit', 'line'], inplace=True)
    # lines.to_sql('line', conn,  if_exists='replace')
    del data['line_name']
    sources = data[['source', 'source_name']].drop_duplicates()
    sources.set_index('source', inplace=True)
    sources.to_sql('source', conn, if_exists='replace')
    del data['source_name']
    del data['object_name']
    data['month'] = 12
    moments = {
        'AP': 'approved',
        'MD': 'modified',
        'DV': 'accrued',
    }
    dfs = []
    for label in moments.keys():
        aux = data.copy()
        aux['moment'] = label
        aux['amount'] = data[moments[label]]
        dfs.append(aux)
    ret = pd.concat(dfs)
    del ret['approved']
    del ret['modified']
    del ret['accrued']
    ret.to_sql('budget', conn, if_exists='replace', index=False)
    return ret

def get_budget_2018():
    data = pd.read_excel('sources/ejecucion_2018.xlsx')
    data.rename(
        columns={
            'EJERCICIO': 'year',
            'INSTITUCION': 'office',
            'FUENTE_FINANC': 'source',
            'UNID. PRESUP.': 'unit',
            'LINEA DE TRAB.': 'line',
            'ESPECIFICO': 'object',
            'PROGRAMADO': 'approved',
            'MODIFICADO': 'modified',
            'DEVENGADO': 'accrued'
        },
        inplace=True
    )
    # del data['PROGRAMADO']
    del data['COMPROMETIDO']
    # Converting code columns to strings
    set_as_codes(data, {
        'office': 4,
        'source': 1,
        'unit': 2,
        'line': 2,
        'object': 5
    })
    data = data.groupby(
        ['year', 'office', 'source', 'unit', 'line', 'object']
    ).sum().reset_index()
    data['month'] = 12
    data['line'] = data['line'].apply(lambda s: s[2:])
    moments = {
        'AP': 'approved',
        'MD': 'modified',
        'DV': 'accrued',
    }
    dfs = []
    for label in moments.keys():
        aux = data.copy()
        aux['moment'] = label
        aux['amount'] = data[moments[label]]
        dfs.append(aux)
    ret = pd.concat(dfs)
    del ret['approved']
    del ret['modified']
    del ret['accrued']
    del ret['MES']
    conn = sqlite3.connect(DBNAME)
    ret.to_sql('budget', conn, if_exists='append', index=False)
    return ret

def get_approved_2019():
    source_file = 'sources/2019_approved.xlsx'
    data = pd.read_excel(source_file)
    data.rename(
        columns={
            'EJERCICIO': 'year',
            'INSTITUCION': 'office',
            # 'NOMB_INSTITUCION': 'office_name',
            'FUENTE DE FINANCIAMIENTÓ': 'source',
            # 'NOMB_FUENTE DE FINANCIAMIENTÓ': 'source_name',
            # 'CLASIFICADOR ECONOMICO': 'economic',
            # 'NOMB_CLASIFICADO ECONOMICO': 'economic_name',
            # 'AREA GESTION': 'area',
            # 'NOMB_AREA GESTION': 'area_name',
            'UNIDAD PRESUPUESTARIA': 'unit',
            # 'NOMB_UNIDAD PRESUPUESTARIA': 'unit_name',
            'LINEA DE TRABAJO': 'line',
            'NOMB_LINEA DE TRABAJO': 'line_name',
            'ESPECIFICO DE GASTO': 'object',
            # 'NOMB_ESPECIFICO DE GASTO': 'object_name',
            'MONTO PROYECTO': 'amount'
        },
        inplace=True
    )
    conn = sqlite3.connect(DBNAME)
    # lines = data[['year', 'office', 'unit', 'line', 'line_name']].drop_duplicates()
    # lines.set_index(['year', 'office', 'unit', 'line'], inplace=True)
    # lines.to_sql('line', conn,  if_exists='append')
    data['moment'] = 'AP'
    data['month'] = '12'
    # Converting code columns to strings
    set_as_codes(data, {
        'office': 4,
        'source': 1,
        'unit': 2,
        'line': 4,
        'object': 5
    })
    data['line'] = data['line'].apply(lambda s: s[2:])
    data = data[[
        'office',
        'year',
        'source',
        'unit',
        'line',
        'object',
        'month',
        'moment',
        'amount'
    ]]
    data.to_sql('budget', conn, if_exists='append', index=False)
    return data

def get_proposed_2017():
    data = pd.read_excel('sources/2017_proposed.xlsx')
    data.rename(
        columns = {
            'ejercicio': 'year',
            'institucion': 'office',
            'fuente_financ': 'source',
            'unid_pres': 'unit',
            'line_pres': 'line',
            'clasif_presup': 'object',
            'monto_recome': 'amount'
        },
        inplace=True
    )
    del data['sector']
    del data['rubro_ecom']
    del data['rubro']
    del data['cuenta']
    data['moment'] = 'PR'
    data['month'] = '12'
    set_as_codes(data, {
        'office': 4,
        'source': 1,
        'unit': 2,
        'line': 2,
        'object': 5
    })
    conn = sqlite3.connect(DBNAME)
    data.to_sql('budget', conn, if_exists='append', index=False)
    conn.close()
    return data
    

def get_proposed_2019():
    source_file = 'sources/2019_proposed.xlsx'
    data = pd.read_excel(source_file)
    data.rename(
        columns={
            'EJERCICIO': 'year',
            'INSTITUCION': 'office',
            # 'NOMB_INSTITUCION': 'office_name',
            'FUENTE DE FINANCIAMIENTÓ': 'source',
            # 'NOMB_FUENTE DE FINANCIAMIENTÓ': 'source_name',
            # 'CLASIFICADOR ECONOMICO': 'economic',
            # 'NOMB_CLASIFICADO ECONOMICO': 'economic_name',
            # 'AREA GESTION': 'area',
            # 'NOMB_AREA GESTION': 'area_name',
            'UNIDAD PRESUPUESTARIA': 'unit',
            # 'NOMB_UNIDAD PRESUPUESTARIA': 'unit_name',
            'LINEA DE TRABAJO': 'line',
            # 'NOMB_LINEA DE TRABAJO': 'line_name',
            'ESPECIFICO DE GASTO': 'object',
            # 'NOMB_ESPECIFICO DE GASTO': 'object_name',
            'MONTO PROYECTO': 'amount'
        },
        inplace=True
    )
    data['moment'] = 'PR'
    data['month'] = '12'
    # Converting code columns to strings
    set_as_codes(data, {
        'office': 4,
        'source': 1,
        'unit': 2,
        'line': 4,
        'object': 5
    })
    data['line'] = data['line'].apply(lambda s: s[2:])
    data = data[[
        'office',
        'year',
        'source',
        'unit',
        'line',
        'object',
        'month',
        'moment',
        'amount'
    ]]
    conn = sqlite3.connect(DBNAME)
    data.to_sql('budget', conn, if_exists='append', index=False)
    conn.close()
    return data

def get_proposed_2020():
    # Two alternative address are given for the source data
    # Choose the most convinient
    source_file = 'sources/2020_proposed.xlsx'
    data = pd.read_excel(source_file)
    # Column names are standarized
    data.rename(columns={
        'EJERCICIO 2020': 'year',
        'INSTITUCION': 'office',
        # 'NOMB_INSTITUCION': 'office_name',
        'FUENTE DE FINANCIAMIENTO': 'source',
        # 'NOMB_FUENTE DE FINANCIAMIENTO': 'source_name',
        # 'RUBRO ECONOMICO': 'economic',
        # 'NOMBRE RUBRO ECONOMICO': 'economic_name',
        # 'AREA GESTION': 'area',
        # 'NOMB_AREA GESTION': 'area_name',
        'UNIDAD PRESUPUESTARIA': 'unit',
        # 'NOMB_UNIDAD PRESUPUESTARIA': 'unit_name',
        'LINEA DE TRABAJO': 'line',
        # 'NOMB_LINEA DE TRABAJO': 'line_name',
        'ESPECIFICO DE GASTO': 'object',
        # 'NOMB_ESPECIFICO DE GASTO': 'object_name',
        'MONTO PROYECTO PRESUPUESTO': 'amount'
    }, inplace=True)
    # Deleting rows in invalid office codes
    invalid_offices = data[data.office.isna()].index
    data = data.drop(invalid_offices)
    invalid_amounts = data[data.amount.isna() == True].index
    data = data.drop(invalid_amounts)
    # Converting code columns to strings
    set_as_codes(data, {
        'office': 4,
        'source': 1,
        'unit': 2,
        'line': 4,
        'object': 5
    })
    # Loading data for secret expenses
    secret_expenses = pd.read_excel('sources/2020_secret_expenses.xlsx')
    # Converting code for secret expenses
    set_as_codes(secret_expenses, {
        'office': 4,
        'source': 1,
        'unit': 2,
        'line': 4,
        'object': 5
    })
    # Concataning datasets
    data = pd.concat([data, secret_expenses], sort=False)
    data['line'] = data['line'].apply(lambda s: s[2:])
    data['moment'] = 'PR'
    data['month'] = 12
    data = data[[
        'office',
        'year',
        'source',
        'unit',
        'line',
        'object',
        'month',
        'moment',
        'amount'
    ]]
    conn = sqlite3.connect(DBNAME)
    data.to_sql('budget', conn, if_exists='append', index=False)
    return data

def get_approved_2020():
    source_file = 'sources/2020_approved.xlsx'
    data = pd.read_excel(source_file)
    # Column names are standarized
    data.rename(columns={
        'EJERCICIO': 'year',
        'INSTITUCION': 'office',
        'NOMB_INSTITUCION': 'office_name',
        'FUENTE DE FINANCIAMIENTÓ': 'source',
        'NOMB_FUENTE DE FINANCIAMIENTÓ': 'source_name',
        # 'RUBRO ECONOMICO': 'economic',
        # 'NOMBRE RUBRO ECONOMICO': 'economic_name',
        'AREA GESTION': 'area',
        'NOMB_AREA GESTION': 'area_name',
        'UNIDAD PRESUPUESTARIA': 'unit',
        'NOMB_UNIDAD PRESUPUESTARIA': 'unit_name',
        'LINEA DE TRABAJO': 'line',
        'NOMB_LINEA DE TRABAJO': 'line_name',
        'ESPECIFICO DE GASTO': 'object',
        'NOMB_ESPECIFICO DE GASTO': 'object_name',
        'MONTO VOTADO': 'amount'
    }, inplace=True)
    # Deleting rows in invalid office codes
    invalid_offices = data[data.office.isna()].index
    data = data.drop(invalid_offices)
    invalid_amounts = data[data.amount.isna() == True].index
    data = data.drop(invalid_amounts)
    # Converting code columns to strings
    set_as_codes(data, {
        'office': 4,
        'source': 1,
        'unit': 2,
        'line': 4,
        'object': 5
    })
    # Loading data for secret expenses
    secret_expenses = pd.read_excel('sources/2020_secret_expenses.xlsx')
    # Converting code for secret expenses
    set_as_codes(secret_expenses, {
        'office': 4,
        'source': 1,
        'unit': 2,
        'line': 4,
        'object': 5
    })
    # Concataning datasets
    data = pd.concat([data, secret_expenses], sort=False)
    data['line'] = data['line'].apply(lambda s: s[2:])
    data['moment'] = 'AP'
    data['month'] = 12
    df = data[[
        'office',
        'year',
        'source',
        'unit',
        'line',
        'object',
        'month',
        'moment',
        'amount'
    ]]
    conn = sqlite3.connect(DBNAME)
    df.to_sql('budget', conn, if_exists='append', index=False)
    unit = data[['year', 'office', 'unit', 'unit_name']]
    unit.set_index(['year', 'office', 'unit'], inplace=True)
    unit.to_sql('unit', conn, if_exists='append')
    line = data[['year', 'office', 'unit', 'line', 'line_name']]
    line.set_index(['year', 'office', 'unit', 'line'], inplace=True)
    line.to_sql('line', conn, if_exists='append')
    conn.close()
    return df

if __name__ == '__main__':
    get_classificator()
    get_structure()
    get_budget_2012_2017()
    get_proposed_2017()
    get_budget_2018()
    get_approved_2019()
    get_proposed_2019()
    get_proposed_2020()
    get_approved_2020()
