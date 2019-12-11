import numpy as np
import pandas as pd
import sqlite3
import dash_table
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import plotly.graph_objs as go
import plotly.express as px

from app import app

DBNAME = 'data/budget.db'
LARGE_INDEX = ['year', 'office', 'office_name', 'level', 'unit', 'line', 'source', 'object', 'moment']
SHORT_INDEX = ['year', 'office', 'office_name', 'level', 'object', 'moment']
RENAMES = {
    'year': 'Año', 
    'office': 'Oficina', 
    'office_name': 'Nombre de la oficina', 
    'level': 'Nivel',
    'object': 'Clasificador',
    'unit': 'Unidad',
    'line': 'Línea',
    'source': 'Fuente',
}
 
moments = {
    'PL': '1. Preliminar',
    'PR': '2. Propuesto',
    'AP': '3. Aprobado',
    'MD': '4. Modificado',
    'DV': '5. Devengado'
}

def get_data(obj='', office='', details=False):
    # A global variable is defined in case data 
    # are not found for the given parameters
    global old_data
    # Optional SQL segment statement for
    # the 'details' condition
    detail_stmt = "unit, line, source," if details else ""
    # The SQL query
    stmt = """
    SELECT 
        year, budget.office AS office, office_name, level, {} 
        '{}' AS object, moment, ROUND(SUM(amount), 2) AS amount
    FROM budget, office
    WHERE 
        object LIKE '{}%' AND 
        budget.office LIKE '{}%' AND 
        budget.office = office.office
    GROUP BY year, level, budget.office, {} moment
    ORDER BY year, level, budget.office, {} moment
    """.format(
            detail_stmt, 
            obj, 
            obj, 
            office, 
            detail_stmt, 
            detail_stmt
        )
    conn = sqlite3.connect(DBNAME)
    data = pd.read_sql(stmt, conn)
    conn.close()
    # Check if data were returned
    if len(data) > 0:
        # Changing labels for 'moment' and 'level' attributes
        labels = data['moment'].unique()
        colnames = [moments[label] for label in labels]
        data['moment'].replace(labels, colnames, inplace=True)
        data['level'].replace(['CG', 'DE'], ['Gobierno central', 'Descentralizadas'], inplace=True)
        data.set_index(LARGE_INDEX if details else SHORT_INDEX, inplace=True)
        df = data.unstack(-1)
        df = df.amount[[item[1] for item in df.columns]]
        df = df.reset_index()
        df.rename(
            columns={
                'year': 'Año', 
                'office': 'Oficina', 
                'office_name': 'Nombre de la oficina', 
                'level': 'Nivel',
                'object': 'Clasificador',
            },
            inplace=True
        )
        if details:
            df.rename(columns={
                    'unit': 'Unidad',
                    'line': 'Línea',
                    'source': 'Fuente',
                },
                inplace=True
            )
        df.to_csv('static/budget_by_object.csv', index=False)
        df.to_excel('static/budget_by_object.xlsx', index=False)
        old_data = df.copy()
        return df
    else:
        return old_data

def make_table():
    data = get_data(details=True) 
    return html.Div([
        dash_table.DataTable(
            id = 'object_table',
            columns = [{'name': col, 'id': col} for col in data.columns],
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
            }
        )
    ])

def generate_figure(obj='', office=''):
    df = get_data(obj, office)
    data = df.groupby('Año').sum() / 1e6
    data = data.reset_index()
    data.replace(0, np.NaN, inplace=True)
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
    return fig

def make_figure():
    return html.Div([
        dcc.Graph(
            id = 'object_plot',
            figure = generate_figure(),
        )
    ])

txt_header = '''
# Explorador de presupuestos
'''

txt_by_object = '''
Este dashboard permite consultar la evolución de los presupuestos de las instituciones
públicas según los clasificadores de egresos. Seleccione el clasificador o la institución
para ver los presupuestos en diferentes momentos: cuando son propuestos a la Asamblea Legislativa,
cuando son aprobados por los diputados, cuando son modificados durante el ejercicio fiscal y,
finalmente, cuando han sido ejecutados (devengados).
'''

def make_object_control():
    global objects
    conn = sqlite3.connect(DBNAME)
    stmt = "SELECT * FROM object WHERE object >= '5'"
    objects = pd.read_sql(stmt, conn)
    conn.close()
    control = html.Div([
        html.Label('Clasificador presupuestario (rubro, cuenta o especifico)'),
        dcc.Dropdown(
            id = 'object_control',
            options = [
                {
                    'label': item[1].object + ' - ' + item[1].object_name, 
                    'value': item[0]
                } for item in objects.iterrows()
            ],
        )
    ])
    return control

def make_office_control():
    global offices
    conn = sqlite3.connect(DBNAME)
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

content = dbc.Container([
    dbc.Row([
        dbc.Col(dcc.Markdown(txt_header))
    ]),
    dbc.Row([
        dbc.Col([
            dcc.Markdown(txt_by_object),
        ]),
    ]),
    dbc.Row([
        dbc.Col([
            make_object_control(),
            make_office_control(),
        ], md=10),
        dbc.Col([
            dbc.Row(html.A('Descargar CSV', href='static/budget_by_object.csv', className='btn btn-primary')),
            dbc.Row(html.A('Descargar XLS', href='static/budget_by_object.xlsx', className='btn btn-primary')),
        ], md=2),
    ]),
    dbc.Row(dbc.Col([
        dcc.Checklist(
            id = 'detail_control',
            options = [
                {
                    'label': 'Incluir detalles (unidad presupuestaria, línea de trabajo y fuente de financiamiento',
                    'value': 0
                }
            ],
            value=[0],
        )
    ])),
    dbc.Row([
        make_figure()
    ]),
    dbc.Row([
        make_table()
    ]),
])

layout = html.Div([content,])

@app.callback(
    Output(component_id='object_table', component_property='columns'),
    [
        Input(component_id='detail_control', component_property='value'),
    ]
)
def remake_table(details):
    data = get_data(details=True if len(details)>0 else   False)
    columns = [{'name': col, 'id': col} for col in data.columns]
    return columns

@app.callback(
    Output(component_id='object_table', component_property='data'),
    [
        Input(component_id='object_control', component_property='value'),
        Input(component_id='office_control', component_property='value'),
        Input(component_id='detail_control', component_property='value'),
    ]
)
def update_table(object_index, office_index, details):
    object_id = '' if object_index == None else objects.iloc[object_index].object
    office_id = '' if office_index == None else offices.iloc[office_index].office
    data = get_data(object_id, office_id, details=True if len(details)>0 else   False)
    return data.to_dict('records')

@app.callback(
    Output(component_id='object_plot', component_property='figure'),
    [
        Input(component_id='object_control', component_property='value'),
        Input(component_id='office_control', component_property='value'),
    ]
)
def update_plot(object_index, office_index):
    object_id = '' if object_index == None else objects.iloc[object_index].object
    office_id = '' if office_index == None else offices.iloc[office_index].office
    fig = generate_figure(object_id, office_id)
    return fig
