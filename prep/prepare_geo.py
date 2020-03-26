import sqlite3
import pandas as pd

departments = {
    '01': 'AHUACHAPAN',
    '02': 'SANTA ANA',
    '03': 'SONSONATE',
    '04': 'CHALATENANGO',
    '05': 'LA LIBERTAD',
    '06': 'SAN SALVADOR',
    '07': 'CUSCATLAN',
    '08': 'LA PAZ',
    '09': 'CABANAS',
    '10': 'SAN VICENTE',
    '11': 'USULUTAN',
    '12': 'SAN MIGUEL',
    '13': 'MORAZAN',
    '14': 'LA UNION',
    '99': 'NC',
    '9999': 'NC'
}

dtype = {
	'location': str,
	'location_name': str
}

def make_location_table():
    conn = sqlite3.connect('master.db')
    df = pd.read_csv('municipalities.csv')
    df.to_sql('location', conn, if_exists='replace', index=False)
    other = pd.DataFrame({
        'location': list(departments.keys()),
        'location_name': list(departments.values())
    })
    other.to_sql('location', conn, if_exists='append', index=False)
    conn.close()

if __name__ == '__main__':
    make_location_table()
