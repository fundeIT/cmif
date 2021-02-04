#!/usr/bin/python

# Purpose:
# This script converts downloaded datasheets into CSV files. Columns and header
# are normalized, so they are ready to be imported into the database.

import os
import re
import csv
import pandas as pd

import utils

DIR_SOURCES = "src/"
DIR_TARGET = "norm/"

def composeColumn(ds, label):
    size = labels[label]['size']
    kind = labels[label]['kind']
    if not label in ds.columns:
        if kind == 'str':
            ds[label] = ""
            return
        else:
            ds[label] = float('nan')
            return
    if kind == 'str':
        if size == '0':
            ds[label] = ds[label].astype(str)
        else:
            ds[label] = ds[label]\
                .astype('Int64')\
                .apply(lambda n: str(n).zfill(int(size)))

def normalizeDataSource(source):
    print(source)
    filename = (DIR_TARGET + source).replace('.xlsx', '.csv')
    if os.path.exists(filename):
        # File has been already downloaded
        return
    ds = pd.read_excel(DIR_SOURCES + source)
    ds.rename(columns=names, inplace=True)
    # Removing invalid rows
    # Is assumed that they have an invalid year
    ds.year = pd.to_numeric(ds.year, errors='coerce')
    ds = ds[pd.notnull(ds.year.isna())]
    for key in ds.columns:
        composeColumn(ds, key)
    ds.to_csv(
        filename, 
        index=False, 
        quoting=csv.QUOTE_NONNUMERIC
    )

names = utils.getNormalizedNames()
labels = utils.getLabels()

if __name__ == "__main__":
    sources = [
        fn 
        for fn in os.listdir(DIR_SOURCES) 
        if fn.find('.xlsx') > 0
    ]
    for source in sources:
        normalizeDataSource(source)
