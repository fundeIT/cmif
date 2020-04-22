# Query utils

import sqlite3
import pandas as pd

DBNAME = 'data/accrued.db'

def get_offices(year):
    """
    Return a dataframe with office's codes and names
    for a given year.
    """
    stmt = """
        SELECT accrued.office, office_name
        FROM accrued
        LEFT JOIN office ON
            accrued.office=office.office
        WHERE year={} AND accrued.office LIKE "%00"
        GROUP BY accrued.office
        ORDER BY accrued.office
    """.format(year)
    conn = sqlite3.connect(DBNAME)
    data = pd.read_sql(stmt, conn)
    conn.close()
    return data

def get_office_name(office, offices_df=pd.DataFrame()):
    """
    Returns the name of an office given its code.
    Optionaly a load office dataframe can be used to query.
    """
    if offices_df.empty:
        stmt = """
            SELECT office_name 
            FROM office
            WHERE office='{}'
        """
        conn = sqlite3.connect(DBNAME)
        c = conn.cursor()
        c.execute(stmt.format(office))
        ret = c.fetchone()
        if ret:
            return ret[0]
        else:
            return 'ND'   
    else:
        row = offices_df.loc[offices_df['office'] == office, 'office_name']
        if len(row) > 0:
            return row.values[0]
        else:
            return 'ND'

