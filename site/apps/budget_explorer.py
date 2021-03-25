import io
import numpy as np
import pandas as pd
import sqlite3
import urllib
import dash_table
from dash_table.Format import Format
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
from dash.exceptions import PreventUpdate
import plotly.graph_objs as go
import plotly.express as px

from app import app
import datamgr

annual_budget = datamgr.AnnualBudget()

def generate_figure(df):
    print("Generate figure: preparing dataset...")
    data = df.groupby('Año').sum() / 1e6
    data = data.reset_index()
    data.replace(0, np.NaN, inplace=True)
    print("Generate figure: building figure attributes...")
    fig = {
        'data': [go.Bar(name=key, x=data['Año'], y=data[key]) for key in data.columns[1:]],
        'layout' : go.Layout(
            xaxis = {
                'title': 'Ejercicios fiscales',
            },
            yaxis = {
                'title': 'Millones USD',
            },
        ),
    }
    print("Generate figure: returning figure")
    return fig

def make_figure():
    data = annual_budget.query() 
    if not isinstance(data, pd.DataFrame):
        return
    return html.Div([
        dcc.Graph(
            id = 'object_plot',
            figure = generate_figure(data),
            # figure = None,
        )
    ])

txt_header = '''
# Explorador de presupuestos
'''

txt_by_object = '''
Este dashboard permite consultar la evolución de los presupuestos de las instituciones públicas según los clasificadores de egresos.
Seleccione el clasificador o la institución para ver los presupuestos en diferentes momentos: cuando son propuestos a la Asamblea
Legislativa, cuando son aprobados por los diputados, cuando son modificados durante el ejercicio fiscal y, finalmente, cuando han
sido ejecutados (devengados).
'''

def make_object_control():
    control = html.Div([
        html.Label('Clasificador presupuestario (rubro, cuenta o especifico)'),
        dcc.Dropdown(
            id = 'object_control',
            options = [
                {
                    'label': item['object'] + ' ' + item['object_name'],
                    'value': item['object']
                }
                for item in annual_budget.objects()
            ],
        )
    ])
    return control

def make_office_control():
    global offices
    conn = sqlite3.connect(annual_budget.dbname)
    stmt = 'SELECT office, office_name FROM office'
    offices = pd.read_sql(stmt, conn)
    conn.close()
    control = html.Div([
        html.Label('Oficina (unidad adminsitrativa)'),
        dcc.Dropdown(
            id = 'office_control',
            options = [
                {
                    'label': item[1].office + ' - ' + item[1].office_name,
                    'value': item[0]
                } for item in offices.iterrows()
            ],
        ),
    ])
    return control

years = annual_budget.years()
api_form = html.Form([
    html.Div([
        html.Label('Ejercicio fiscal: ', htmlFor='year'),
        dcc.Dropdown(
            id = 'api_budget_year',
            options = [{'label': year, 'value': year} for year in years],
            value = years[-1], 
        ),
    ], className='form-group'),
    html.Div([
        html.Label('Incluir:', htmlFor='struct'),
        dcc.Checklist(
            id='api_budget_include',
            options=[
                {'label': ' Estructura presupuestaria', 'value': 'struct'},
                {'label': ' Fuentes de financiamiento', 'value': 'source'},

            ]
        ),
    ], className='form-group'),
    html.Div([
        html.Label('Nivel de detalle', htmlFor='source'),
        dcc.Dropdown(
            id = 'api_budget_code_len',
            options = [
                {'label': 'Rubro', 'value': 2},
                {'label': 'Cuenta', 'value': 3},
                {'label': 'Específico', 'value': 5},
            ],
            value=2,
        )
    ], className='form-group'),
    html.Div([
        html.A(
            'Descargar CSV',
            id='api_budget_download',
            className='btn btn-primary'
        ),
    ], className='form-group'),
    html.Div([
        dcc.Markdown("""
        Diccionarios:

        - [Oficinas](/api/v1/offices)
        - [Clasificador presupuestario](/api/v1/budgetary_codes)
        """)
    ])
    
])

content = dbc.Container([
    dbc.Row([
        dbc.Col(dcc.Markdown(txt_header))
    ]),
    dbc.Row([
        dbc.Col([
            dbc.Row(dbc.Col([
                    dcc.Markdown(txt_by_object),
                ])),
                dbc.Row(dbc.Col([
                    make_object_control(),
                ])),
                dbc.Row(dbc.Col([
                    make_office_control(),
                ])),
        ], md=4),
        dbc.Col(
            dbc.Tabs([
                dbc.Tab([
                    make_figure()
                ], label='Gráfica', tab_id='plot'),
                dbc.Tab(api_form, label='API', tab_id='api'),
            ], id='tabs'),
        ),
    ]),
])

layout = html.Div([content,])

@app.callback(
    [
        Output(component_id='object_plot', component_property='figure'),
    ],
    [
        Input(component_id='object_control', component_property='value'),
        Input(component_id='office_control', component_property='value'),
    ],
)
def update_outputs(object_index, office_index):
    object_id = '' if object_index == None \
        else annual_budget.objects()[object_index]['object']
    office_id = '' if office_index == None \
        else offices.iloc[office_index].office
    data = annual_budget.query(object_id, office_id)
    fig = generate_figure(data)
    return fig

# @app.callback(
#     Output(component_id='download_csv', component_property='href'),
#     [
#         Input(component_id='object_table', component_property='data'),
#     ]
# )
# def download_csv(data):
#     df = pd.DataFrame(data)
#     csv_string = df.to_csv(index=False)
#     csv_string = 'data:text/csv;charset=utf-8,' + urllib.parse.quote(csv_string)
#     return csv_string
# 
# @app.callback(
#     Output(component_id='download_xlsx', component_property='href'),
#     [
#         Input(component_id='object_table', component_property='data'),
#     ]
# )
# def download_xlsx(data):
#     df = pd.DataFrame(data)
#     output = io.BytesIO()
#     writer = pd.ExcelWriter(output)
#     df.to_excel(writer, index=False)
#     writer.save()
#     xlsx_string = "data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;charset=utf-8," + urllib.parse.quote(output.getvalue())
#     return xlsx_string
# 
# @app.callback(
#     Output(component_id='api_budget_download', component_property='href'),
#     [
# 
#         Input(component_id='api_budget_year', component_property='value'),
#         Input(component_id='api_budget_include', component_property='value'),
#         Input(component_id='api_budget_code_len', component_property='value'),
#     ]
# )
# def api_download_budget(year, include, code_len):
#     include = include if include else []
#     struct = 1 if 'struct' in include else 0
#     source = 1 if 'source' in include else 0
#     return f"/api/v1/budget?year={year}&struct={struct}&source={source}&code_len={code_len}"
