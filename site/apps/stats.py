# Monitor to budget execution
#
# (2020) Fundación Nacional para el Desarrollo
#
# Contributors:
#   Jaime Lopez <jailop AT gmail DOT com>

import io
import os
import time
import urllib
import numpy as np
import pandas as pd
import dash_table
from dash_table.Format import Format
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import plotly.graph_objs as go
import plotly.express as px

from app import app

STATSFILE = 'stats.csv'
LOGPATH = 'log/'

def get_data():
    if not os.path.isfile(STATSFILE):
        with open(STATSFILE, "w") as fd:
            fd.write("month,hits,updated\n")
    stats = pd.read_csv(STATSFILE)
    stats['month'] = stats.month.astype(str)
    log_files = os.listdir(LOGPATH)
    for lf in log_files:
        if lf == 'README.md':
            continue
        updated = os.path.getmtime(LOGPATH + lf)
        # Checking if the has a record
        if not lf in stats.month.values:
            hits = len(open(LOGPATH + lf, "r").readlines())
            rec = {'month': lf, 'hits': hits, 'updated': updated}
            stats = stats.append(rec, ignore_index=True)
        else:
            if stats.loc[stats.month == lf, 'updated'].values[0] < updated:
                hits = len(open(LOGPATH + lf, "r").readlines())
                stats.loc[stats.month == lf, 'updated'] = updated
                stats.loc[stats.month == lf, 'hits'] = hits
    stats.to_csv("stats.csv", index=False)
    return stats

def make_table():
    data = get_data()
    columns = [{'name': col, 'id': col} for col in data.columns]
    return html.Div([
        dash_table.DataTable(
            id = 'stats_table',
            columns = columns,
            data = data.to_dict('records'),
            sort_action = 'native',
            style_data = {
                'whiteSpace': 'normal',
                'height': 'auto'
            },
            style_as_list_view = True,
            style_header = {
                'backgroundColor': 'white',
                'fontWeight': 'bold'
            },
            page_size = 50,
            fill_width = False,
        )
    ])

def pretty_month(month):
    month = str(month)
    month = "M" + month[:4] + "-" + month[4:]
    return month

def generate_figure(df):
    x = [pretty_month(m) for m in df.month.values]
    y = df.hits.values / 1e3
    fig = {
        'data': [
                go.Bar(x=x, y=y),
            ],
        'layout' : go.Layout(
            xaxis = {
                'title': 'Meses',
            },
            yaxis = {
                'title': 'Hits (miles)',
            },
        ),
    }
    return fig

def make_figure():
    return html.Div([
        dcc.Graph(
            id = 'stats_plot',
            figure = generate_figure(get_data()),
        )
    ])

txt_header = '''
# Estadísticas de uso del sitio web
'''

txt_by_object = '''
En esta sección se presentan las estadísticas mensuales de uso del sitio web del
Centro de Monitoreo e Incidencia Fiscal. El uso del sitio está medido en hits,
es decir páginas o recursos vistos por los usuarios.
'''

content = dbc.Container([
    dbc.Row([
        dbc.Col(dcc.Markdown(txt_header))
    ]),
    dbc.Row([
        dbc.Col([
            dbc.Row(dbc.Col([
                dcc.Markdown(txt_by_object),
            ])),
        ], md=4),
        dbc.Col(
            dbc.Tabs([
                dbc.Tab([
                    dbc.Row(dbc.Col([
                        make_figure()
                    ])),
                ], label='Gráfica', tab_id='plot'),
                dbc.Tab([
                    dbc.Row(dbc.Col([
                        html.A(
                            'Descargar CSV',
                            download='stats.csv',
                            id='stats_csv',
                            className='btn btn-primary'
                        ),
                        ' ',
                        html.A(
                            'Descargar XLS',
                            download='stats.xlsx',
                            id='stats_xlsx',
                            className='btn btn-primary'
                        ),
                    ])),
                    dbc.Row(dbc.Col(make_table())),
                ], label='Tabla', tab_id='table'),
            ], id='tabs'),
        className='text-center'),
    ])
])

layout = html.Div([content,])

@app.callback(
    Output(component_id='stats_csv', component_property='href'),
    [
        Input(component_id='stats_table', component_property='data'),
    ]
)
def download_csv(data):
    df = pd.DataFrame(data)
    csv_string = df.to_csv(index=False)
    csv_string = 'data:text/csv;charset=utf-8,' + urllib.parse.quote(csv_string)
    return csv_string

@app.callback(
    Output(component_id='stats_xlsx', component_property='href'),
    [
        Input(component_id='stats_table', component_property='data'),
    ]
)
def download_xlsx(data):
    df = pd.DataFrame(data)
    output = io.BytesIO()
    writer = pd.ExcelWriter(output)
    df.to_excel(writer, index=False)
    writer.save()
    xlsx_string = "data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;charset=utf-8," + urllib.parse.quote(output.getvalue())
    return xlsx_string
