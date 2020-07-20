#!/bin/usr/python

import sys
import re
import lxml
import getopt
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.select import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import pandas as pd
from lxml import html

class Procurement:
    def __init__(self):
        pass
    def get_driver(self, headless=True):
        options = Options()
        if headless:
            options.add_argument('--headless')
        driver = webdriver.Chrome(options=options)
        # driver = webdriver.Chrome()
        driver.implicitly_wait(10)
        return driver
    def update(self, start=None, end=None, wait=0):
        pass
    def save(filename):
        self.df.to_csv(filename, index=False)

class PTF(Procurement):
    def __init__(self):
        super().__init__()
        self.url = 'https://www.transparenciafiscal.gob.sv/ptf/es/PTF2-Compras_Publicas.html'
        self.xpaths = {
            'type': '//*[@id="dselecttype"]',
            'office': '//*[@id="dselectinst"]',
            'start': '//*[@id="dini"]',
            'end': '//*[@id="dfin"]',
            'download': '/html/body/div[5]/div/div[2]/div/div/div/div[3]/div[1]/div/div[4]/a',
            'all_process': '/html/body/div[5]/div/div[2]/div/div/div/div[2]/div[2]/a',
            'awarded': '/html/body/div[5]/div/div[2]/div/div/div/div[2]/div[1]/a',
            'paginator': '/html/body/div[5]/div/div[2]/div/div/div/div[3]/div[2]',
            'table': '/html/body/div[5]/div/div[2]/div/div/div/div[3]/div[3]/div/table',
            # 'table': '/html/body/div[5]/div/div[2]/div/div/div/div[3]/div[3]/div',
        }
    def update(self, start, end, wait=0):
        driver = self.get_driver(headless=False)
        driver.get(self.url)
        
        type_ctrl = Select(driver.find_element_by_xpath(self.xpaths['type']))
        office_ctrl = Select(driver.find_element_by_xpath(self.xpaths['office']))
        
        start_ctrl = driver.find_element_by_xpath(self.xpaths['start'])
        end_ctrl = driver.find_element_by_xpath(self.xpaths['end'])
        all_process_ctrl = driver.find_element_by_xpath(self.xpaths['all_process'])
        all_process_ctrl.click()
        driver.execute_script(f"arguments[0].value = '{start}'", start_ctrl)
        driver.execute_script(f"arguments[0].value = '{end}'", end_ctrl)
        #start_ctrl.send_keys(start)
        #end_ctrl.send_keys(end)
        
        
        types = {el.get_attribute("value"):el.text for el in type_ctrl.options}
        offices = {el.get_attribute("value"):el.text for el in office_ctrl.options}
        
        data = []
        for t in types.keys():
            type_ctrl.select_by_value(t)
            for o in offices.keys():
                print(o)
                office_ctrl.select_by_value(o)
                time.sleep(10)
                try:
                    table_ctrl = driver.find_element_by_xpath(self.xpaths['table'])
                    content = html.fromstring(table_ctrl.get_attribute('innerHTML'))
                    print(content.text)
                    aux = pd.read_html(content.text)
                    print(len(aux))
                    data.append(aux)
                except:
                    print(o, ' failed')
        driver.close()
        df = pd.concat(data)
        df.to_csv('results.csv')
        return df
    
class Comprasal(Procurement):
    def __init__(self):
        super().__init__(self)
        # Scheme for dates: DD/MM/YYYY
        self.start = start
        self.end = end
        self.url = 'https://www.comprasal.gob.sv/comprasal_web/resultados'
        self.xpaths = {
            'start': '//*[@id="comprasal_1:fecha_desde_input"]',
            'end': '//*[@id="comprasal_1:fecha_hasta_input"]',
            'search': '//*[@id="comprasal_1:j_idt105"]',
            'table': '//*[@id="comprasal_1:principal"]',
            'next_page': '/html/body/div[1]/div[2]/div/form/table/tbody/tr[1]/td/div/div[2]/a[3]',
            'paginator': '/html/body/div[1]/div[2]/div/form/table/tbody/tr[1]/td/div/div[2]/span',
        }
    def update(self, start, end, wait=0):
        driver = self.get_driver()
        driver.get(self.url)
        # Setting controls
        starting_date_box = driver.find_element_by_xpath(self.xpaths['start'])
        ending_date_box = driver.find_element_by_xpath(self.xpaths['end'])
        search_button = driver.find_element_by_xpath(self.xpaths['search'])
        # Getting parameters
        starting_date_box.send_keys(self.start)
        ending_date_box.send_keys(self.end)
        search_button.click()
        paginator_ctrl = driver.find_element_by_xpath(self.xpaths['paginator'])
        limit = int(re.findall('\d+', paginator_ctrl.text)[-1])
        # print('%d pages to recover' % limit)
        # Getting the data
        tables = []
        for i in range(limit):
            print('Page %d/%d' % (i, limit, ))
            while True:
                paginator_ctrl = driver.find_element_by_xpath(self.xpaths['paginator'])
                pos = int(re.findall('\d+', paginator_ctrl.text)[0])
                if pos == i + 1:
                    break
                table = driver.find_element_by_xpath(self.xpaths['table'])
                content = table.get_attribute('innerHTML')
                data = pd.read_html(content)
                tables.append(data[0])
                next_page_ctrl = driver.find_element_by_xpath(self.xpaths['next_page'])
                next_page_ctrl.click() 
        # Saving results
        self.df = pd.concat(tables)
        driver.close()
        print('Dataset completed')

if __name__ == '__main__':
    wait = 0
    opts, args = getopt.getopt(sys.argv[1:], "s:e:w:", ["start", "end", "wait"])
    for o, a in  opts:
        if o in ['-s', '--start']:
            start = a
        elif o in ['-e', '--end']:
            end = a
        elif o in ['-w', '--wait']:
            wait = int(a)
        else:
           assert False, "unhandled option"
    p = Comprasal()
    p.update(start, end, wait)
    p.save('compras.csv')
