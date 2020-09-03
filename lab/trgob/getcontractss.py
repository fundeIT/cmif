import pandas as pd
import requests
import re
from lxml import html
import csv

colnames = [
    'Código de adquisición o contratación',
    'Área institucional',
    'Objeto',
    'Monto',
    'Nombre de la contraparte',
    'Plazos de cumplimiento',
    'Tipo de contratación',
    'Fecha de contrato / Órden de compra',
    'Código de contrato / Órden de compra',
    'Características de la contraparte',
    'Archivo adjunto',
    'Fecha de creación',
    'Fecha de última actualización',
    'office'
]

def contract_detail(url):
    page = html.fromstring(requests.get(url).text)
    sections = page.xpath('/html/body/main/div/div/div[2]/div[2]/div/div/div')
    labels = [sections[i].xpath('strong/text()')[0] for i in range(0, len(sections), 2)]
    content = [sections[i].xpath('text()')[0].strip() for i in range(1, len(sections), 2)]
    card = {labels[i]: content[i] for i in range(len(labels))}
    card['Archivo adjunto'] = page.xpath('/html/body/main/div/div/div[2]/div[2]/div/div[12]/div[2]/a/@href')[0]
    return card

cl = pd.read_csv('list.csv')

fin = open('contracts.csv', 'w')
writer = csv.DictWriter(fin, fieldnames=colnames)
writer.writeheader()
for i, j in cl.iterrows():
    try:
        contract = contract_detail(cl.iloc[i]['list'])
        contract['office'] = cl.iloc[i]['office']
        writer.writerow(contract)
        print(i, contract['office'], end='\r')
    except:
        pass

fin.close()
