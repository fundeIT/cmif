#!/usr/bin/python

import csv
import sqlite3
import pandas as pd

def annual_proposed_2021():
    # Getting data
    source = 'norm/annual-proposed-2021.csv'
    data = pd.read_csv(source, dtype=str)
    # Adjusting parameters
    data['proposed'] = data.proposed.astype(float)
    data['moment'] = 'PR'
    data['month'] = 0 
    data = data.groupby(['office', 'year', 'source', 'unit', 'line', 'object', 
        'month', 'moment' ]).sum()['proposed'].reset_index()
    data.rename(columns={'proposed': 'amount'}, inplace=True)
    # Removing old records from database
    conn = sqlite3.connect('budget.db')
    c = conn.cursor()
    c.execute("""
        DELETE FROM budget 
            WHERE year = 2021 and moment = 'PR'
    """)
    conn.commit()
    # Updating the database
    data.to_sql('budget', conn, if_exists='append', index=False)
    
if __name__ == '__main__':
    annual_proposed_2021()
