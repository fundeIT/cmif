# Update accrued DB for December 2020

import sqlite3
import pandas as pd

DB = "../master.db"

# Removing all records for Jan-Mar/2021
stmt = "DELETE FROM accrued WHERE year=2021 AND (month=1 OR month=2 OR month=3)"
con = sqlite3.connect(DB)
cur = con.cursor()
cur.execute(stmt)
con.commit()
con.close()

# Getting data from ALAC server
url = "https://alac.funde.org/docs/608c176ae278c42e4e54d7fd"
data = pd.read_excel(url, sheet_name="accrued")
data = data[data.columns[:-1]].dropna()

# Preparing the dataset
data['year'] = data.year.apply(int)
data['office'] = data.office.apply(lambda x: str(int(x)).zfill(4))
data['program'] = data.program.apply(lambda x: str(int(x)).zfill(4))
data['source'] = data.source.apply(int)
data['month'] = data.month.apply(int)
data['financier'] = ""
data['area'] = ""
data['shifted'] = data['modified'] - data['approved']
data = data[[
    'year', 'area', 'office', 'program', 
    'source', 'financier', 'object', 'month', 
    'approved', 'modified', 'accrued', 'shifted'
]]

# Updating the database
con = sqlite3.connect(DB)
data.to_sql("accrued", con, if_exists="append")
con.close()
