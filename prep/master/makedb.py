#!/usr/bin/python

import os
import re
import sqlite3
import pandas as pd

import utils

DB = "../master.db"
DIR_NORMS = "norm/"

fields = utils.getFieldNames()
labels = utils.getLabels()

if __name__ == "__main__":
    sources = [
        fn 
        for fn in os.listdir(DIR_NORMS) 
        if re.match('monthly-[0-9a-z\-]+\.pickle', fn)
    ]
    flag_first = True
    conn = sqlite3.connect(DB)
    for source in sources: 
        print(source)
        try:
            data = pd.read_pickle(DIR_NORMS + source)
        except:
            print('{} cannot be read'.format(source))
            continue
        try:
            data = data[fields]
        except:
            print('Invalid fields')
            print(set(data.columns).differente(set(fields)))
            print(set(fields).difference(set(data.columns)))
            continue
        data['shifted'] = data['modified'] - data['approved']
        if flag_first:
            data.to_sql('accrued', conn, if_exists='replace', index=True)
            flag_first = False
        else:
            data.to_sql('accrued', conn, if_exists='append',  index=True)
    # Removing invalid records
    c = conn.cursor()
    c.execute("DELETE FROM accrued WHERE year is NULL")
    conn.commit()
    conn.close()


        
