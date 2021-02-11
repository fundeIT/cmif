# Accrued Budget Nov-Dec/2020

import pandas as pd
import csv
import utils
import normalize

names = utils.getNormalizedNames()
labels = utils.getLabels()
fields = utils.getFieldNames()

url = "https://alac.funde.org/docs/602486878ad34f5dd12eb1e3"
data = pd.read_excel(url, sheet_name="EJECUCIÓN")
data.columns

nov = data[::2]
dec = data[1::2]

print("Duplicates in Nov. 2020: ", True in nov.duplicated())
print("Duplicates in Dec. 2020: ", True in dec.duplicated())

nov = nov.rename(columns=names)
dec = dec.rename(columns=names)

nov['month'] = 11
dec['month'] = 12

for ds, filename in [(nov, "norm/monthly-202011.csv"), (dec, "norm/monthly202012.csv")]:
    for key in ds.columns:
        normalize.composeColumn(ds, key)
    for field in fields:
        if not field in ds.columns:
            ds[field] = ''
    ds.to_csv(
        filename,
        index=False,
        quoting=csv.QUOTE_NONNUMERIC
    )
    ds.to_pickle(filename.replace('.csv', '.pickle'))
