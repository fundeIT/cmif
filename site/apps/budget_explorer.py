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
import plotly.graph_objs as go
import plotly.express as px

from app import app

DBNAME = 'data/budget.db'

RENAMES = {
    'year': 'Año',
    'office': 'Oficina',
    'office_name': 'Nombre de la oficina',
    'level': 'Nivel',
    'unit': 'Unidad',
    'unit_name': 'Nombre de la unidad',
    'line': 'Línea',
    'line_name': 'Nombre de la línea',
    'source': 'Fuente',
    'object': 'Clasificador',
    'moment': 'Momento',
}
INDEX_LARGE = list(RENAMES.keys())
INDEX_SHORT = ['year', 'office', 'office_name', 'level', 'object', 'moment']

MOMENTS = {
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
    detail_stmt = """
        budget.unit, unit_name, budget.line, line_name, source,
    """ if details else ""
    join_stmt = """
    LEFT JOIN unit ON
        budget.year = unit.year AND
        budget.office = unit.office AND
        budget.unit = unit.unit
    LEFT JOIN line ON
        budget.year = line.year AND
        budget.office = line.office AND
        budget.unit = line.unit AND
        budget.line = line.line
    """ if details else ""
    # The SQL query
    stmt = """
    SELECT
        budget.year, budget.office AS office, office_name, level, {}
        '{}' AS object, moment, ROUND(SUM(amount), 2) AS amount
    FROM budget, office
    {}
    WHERE
        object LIKE '{}%' AND
        budget.office LIKE '{}%' AND
        budget.office = office.office
    GROUP BY budget.year, level, budget.office, {} moment
    ORDER BY budget.year, level, budget.office, {} moment
    """.format(
            detail_stmt,
            obj,
            join_stmt,
            obj,
            office,
            detail_stmt,
            detail_stmt,
        )
    conn = sqlite3.connect(DBNAME)
    data = pd.read_sql(stmt, conn)
    conn.close()
    # Check if data were returned
    if len(data) > 0:
        # Changing labels for 'moment' and 'level' attributes
        labels = data['moment'].unique()
        colnames = [MOMENTS[label] for label in labels]
        data['moment'].replace(labels, colnames, inplace=True)
        data['level'].replace(
            ['CG', 'DE'],
            ['Gobierno central', 'Descentralizadas'],
            inplace=True
        )
        data.set_index(INDEX_LARGE if details else INDEX_SHORT, inplace=True)
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
                    'unit_name': 'Nombre de la unidad',
                    'line': 'Línea',
                    'line_name': 'Nombre de la línea',
                    'source': 'Fuente',
                },
                inplace=True
            )
        # df.to_csv('static/budget.csv', index=False)
        # df.to_excel('static/budget.xlsx', index=False)
        old_data = df.copy()
        return df
    else:
        return old_data

def make_table():
    data = get_data()
    columns = [{'name': col, 'id': col} for col in data.columns]
    for i, col in enumerate(columns):
        if col['name'] in MOMENTS.values():
            columns[i]['type'] = 'numeric'
            columns[i]['format'] = Format(group=',', precision=2, scheme='f')
    return html.Div([
        dash_table.DataTable(
            id = 'object_table',
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
            locale_format = {
                'decimal': '2',
                'symbol': ['$', ','],
                'separate_4digits': True,
            }
        )
    ])

def generate_figure(df):
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
            figure = generate_figure(get_data()),
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

def make_check_details():
    return dcc.Checklist(
        id = 'detail_control',
        options = [
            {
                'label': 'Incluir detalles',
                'value': 0
            }
        ],
        value=[],
    )


def get_years():
    stmt = 'SELECT DISTINCT(year) FROM budget ORDER BY year'
    conn = sqlite3.connect(DBNAME)
    c = conn.cursor()
    years = [year[0] for year in c.execute(stmt)] 
    conn.close()
    return years

years = get_years() 

history = html.Ul([
    html.Li(
        '''
        2020-03-24: Se agregaron los presupuestos de los años 2007-2011, así
        como el presupuesto modificado y ejecutado de 2019
        '''
    )
])

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
                dbc.Tab([
                    dbc.Row(dbc.Col([
                        make_check_details(),
                        html.A(
                            'Descargar CSV',
                            # href='static/budget_by_object.csv',
                            download='budget.csv',
                            id='download_csv',
                            className='btn btn-primary'
                        ),
                        ' ',
                        html.A(
                            'Descargar XLS',
                            # href='static/budget_by_object.xlsx',
                            download='budget.xlsx',
                            id='download_xlsx',
                            className='btn btn-primary'
                        ),
                    ])),
                    dbc.Row(dbc.Col([
                        make_table(),
                    ])),
                ], label='Tabla', tab_id='table'),
                dbc.Tab(api_form, label='API', tab_id='api'),
                dbc.Tab(history, label='Historial', tab_id='history'),
            ], id='tabs'),
        ),
    ]),
])

layout = html.Div([content,])

@app.callback(
    [
        Output(component_id='object_table', component_property='data'),
        Output(component_id='object_plot', component_property='figure'),
        Output(component_id='object_table', component_property='columns'),
    ],
    [
        Input(component_id='object_control', component_property='value'),
        Input(component_id='office_control', component_property='value'),
        Input(component_id='detail_control', component_property='value'),
    ]
)
def update_outputs(object_index, office_index, details):
    object_id = '' if object_index == None \
        else objects.iloc[object_index].object
    office_id = '' if office_index == None \
        else offices.iloc[office_index].office
    data = get_data(object_id, office_id,
        details=True if len(details)>0 else   False)
    fig = generate_figure(data)
    columns = [{'name': col, 'id': col} for col in data.columns]
    return data.to_dict('records'), fig, columns

@app.callback(
    Output(component_id='download_csv', component_property='href'),
    [
        Input(component_id='object_table', component_property='data'),
    ]
)
def download_csv(data):
    df = pd.DataFrame(data)
    csv_string = df.to_csv(index=False)
    csv_string = 'data:text/csv;charset=utf-8,' + urllib.parse.quote(csv_string)
    return csv_string

@app.callback(
    Output(component_id='download_xlsx', component_property='href'),
    [
        Input(component_id='object_table', component_property='data'),
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

@app.callback(
    Output(component_id='api_budget_download', component_property='href'),
    [

        Input(component_id='api_budget_year', component_property='value'),
        Input(component_id='api_budget_include', component_property='value'),
        Input(component_id='api_budget_code_len', component_property='value'),
    ]
)
def api_download_budget(year, include, code_len):
    include = include if include else []
    struct = 1 if 'struct' in include else 0
    source = 1 if 'source' in include else 0
    return f"/api/v1/budget?year={year}&struct={struct}&source={source}&code_len={code_len}"
