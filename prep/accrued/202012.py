# Update accrued DB for December 2020

import sqlite3
import pandas as pd

DB = "../master.db"

# Removing all records for Dec. 2020
stmt = "DELETE FROM accrued WHERE year=2020 AND month=12"
con = sqlite3.connect(DB)
cur = con.cursor()
cur.execute(stmt)
con.commit()
con.close()

# Getting data from ALAC server
url = "https://alac.funde.org/docs/607cccdbb068247317e66077"
data = pd.read_excel(url, sheet_name="EJECUCIÓN")

# Preparing the dataset
data = data[data.month == 12]
data['office'] = data.office.apply(lambda x: str(x).zfill(4))
data['program'] = data.line.apply(lambda x: str(x).zfill(4))
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
