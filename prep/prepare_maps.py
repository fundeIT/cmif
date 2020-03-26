import sqlite3
import numpy as np
import pandas as pd
import geopandas

import utils

conn = sqlite3.connect('master.db')

stmt = """
    SELECT 
        department, department_name, 
        municipality, municipality_name
    FROM
        (SELECT 
            location AS department, 
            location_name as department_name 
        FROM location
        WHERE LENGTH(location) <= 2) AS dep,
        (SELECT 
            location AS municipality, 
            location_name as municipality_name 
        FROM location
        WHERE LENGTH(location) > 2) AS mun
    WHERE department = municipality / 100
"""
location = pd.read_sql(stmt, conn)
conn.close()

location['department'] = location['department'].apply(lambda s: str(s).zfill(2))
location['municipality'] = location['municipality'].apply(lambda s: str(s).zfill(4))
location['municipality_name'] = location['municipality_name'].apply(lambda s: utils.asciify(s).upper())

sv = geopandas.read_file('geo/SLV_adm2.shp')
sv['department_name'] = sv['NAME_1'].apply(lambda s: utils.asciify(s.upper()))
sv['municipality_name'] = sv['NAME_2'].apply(lambda s: utils.asciify(s.upper()))
sv = sv[['department_name', 'municipality_name', 'geometry']]

idem_names = [
    ('CABANAS', 'DOLORES', 'VILLA DOLORES'),
    ('CHALATENANGO', 'SAN ANTONIO DE LA CRUZ', 'SAN ANTONIO LA CRUZ'),
    ('LA LIBERTAD', 'NUEVA SAN SALVADOR', 'SANTA TECLA'),
    ('LA LIBERTAD', 'OPICO', 'SAN JUAN OPICO'),
    ('LA UNION', 'SAN JOSE', 'SAN JOSE LA FUENTE'),
    ('SAN MIGUEL', 'SAN ANTONIO', 'SAN ANTONIO DEL MOSCO'),
    ('SAN MIGUEL', 'SAN RAFAEL', 'SAN RAFAEL ORIENTE'),
    ('SAN SALVADOR', 'DELGADO', 'CIUDAD DELGADO'),
    ('SAN VICENTE', 'SAN ILDEFONSO', 'SAN IDELFONSO'),
    ('SONSONATE', 'NAHULINGO', 'NAHUILINGO'),
    ('SONSONATE', 'SANTO DOMINGO', 'SANTO DOMINGO DE GUZMAN')
]
for idem in idem_names:
    sv.loc[
        (sv.department_name == idem[0]) & (sv.municipality_name == idem[1]), 
        'municipality_name'
    ] = idem[2]

municipality = sv.merge(location, on=['department_name', 'municipality_name'], how='left')
municipality = municipality[['municipality', 'geometry']]

sv = geopandas.read_file('geo/SLV_adm1.shp')
sv['department_name'] = sv['NAME_1'].apply(lambda s: utils.asciify(s.upper()))
sv = sv[['department_name', 'geometry']]

department = sv.merge(location, on=['department_name'], how='left')
department = department[['department', 'geometry']]

# municipality.rename(columns={'municipality': ' location'}, inplace=True)
# department.rename(columns={'department': 'location'}, inplace=True)

municipality.to_file('shp/municipality.shp')
department.to_file('shp/department.shp')
