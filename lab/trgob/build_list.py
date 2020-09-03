import re
import requests
from lxml import html
import pandas as pd

urls = {
    'offices' : 'https://www.transparencia.gob.sv/api/v1/institutions.json',
    'contracts' : 'https://www.transparencia.gob.sv/institutions/{}/contracts'
}

xpaths = {
    'contracts' : '//div[@class="columns small-24 medium-16 large-12"]/a/@href',
    'pagination' : '//div[@class="pagination"]/a/text()'
}

def normalize_acronym(acron):
    aux = re.sub(r'[^\w]', ' ', acron)
    aux = re.sub(r'\s+', '-', aux)
    return aux.lower()

def contract_list(office):
    contracts = []
    url = urls['contracts'].format(office)
    page = html.fromstring(requests.get(url).text)
    contracts += page.xpath(xpaths['contracts'])
    pagination = page.xpath(xpaths['pagination'])
    if len(pagination) > 0:
        last_page = int(pagination[pagination.index('Siguiente') - 1])
        for i in range(2, last_page + 1):
            page = html.fromstring(requests.get(url + '?page=%d' % i).text)
            contracts += page.xpath(xpaths['contracts'])
    return contracts

def build_list():
    offices = pd.read_json(urls['offices'])
    offices['key'] = offices['acronym'].apply(normalize_acronym)
    offices[['key', 'name']].to_csv('offices.csv', index=False)
    dfs = []
    for k in offices['key'].values:
        try:
            cl = contract_list(k)
            dfs.append(pd.DataFrame({'office': k, 'list': cl}))
            print(k, ':', len(cl))
        except:
            pass
    return pd.concat(dfs)

if __name__ == '__main__':
    contracts_list = build_list()
    contracts_list.to_csv('list.csv', index=False)
