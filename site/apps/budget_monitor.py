# Monitor to budget execution
#
# (2020) Fundación Nacional para el Desarrollo
#
# Contributors:
#   Jaime Lopez <jailop AT gmail DOT com>

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

DBNAME = 'data/accrued.db'
DBDICT = 'data/master.db'

COLNAMES = {
    'year': 'Año',
    'office': 'Oficina',
    'office_name': 'Nombre de la oficina',
    'month': 'Mes',
    'approved': 'Aprobado',
    'shifted': 'Modificaciones',
    'modified': 'Modificado',
    'accrued': 'Devengado'
}

def get_years():
    stmt = 'SELECT DISTINCT(year) FROM accrued ORDER BY year'
    conn = sqlite3.connect(DBNAME)
    c = conn.cursor()
    res = c.execute(stmt)
    ret = [r[0] for r in res]
    conn.close()
    return ret

def get_last_year():
    years = get_years()
    return years[-1] # The last one

def get_offices(year=None):
    if year == None:
        year = get_last_year()
    stmt = """
        SELECT accrued.office, office_name
        FROM accrued
        LEFT JOIN office ON
            accrued.office=office.office
        WHERE year={}
        GROUP BY accrued.office
        ORDER BY accrued.office
    """.format(year)
    conn = sqlite3.connect(DBNAME)
    data = pd.read_sql(stmt, conn)
    conn.close()
    return data

def get_first_office(year=None):
    data = get_offices()
    return data.iloc[0]['office']

YEAR = get_last_year()
OFFICE = get_first_office(YEAR)

def get_structure(year, office):
    stmt = """
        SELECT est, est_name FROM
            (
	            SELECT year, office, line AS est, line_name AS est_name 
	                FROM line
	            UNION
	            SELECT year, office, unit AS est, unit_name AS est_name 
	                FROM unit
            )
        WHERE year={} AND office='{}'
        ORDER BY year, office, est, est_name
    """.format(year, office)
    conn = sqlite3.connect(DBDICT)
    data = pd.read_sql(stmt, conn)
    conn.close()
    return data

def get_data(year=None, office=None, unit='', line='', classifier='', cum=False):
    global old_data
    if year == None:
        year = get_last_year()
    if office == None:
        office = get_first_office(year)
    opt_line = "  AND line LIKE '{}%' ".format(line) \
        if line != None and line != '' \
        else ''
    class_line = " AND object LIKE '{}%' ".format(classifier) \
        if classifier != None and classifier != '' \
        else ''
    stmt = """
        SELECT
            year, accrued.office, office_name, month,
            SUM(approved) AS approved,
            SUM(shifted) AS shifted,
            SUM(modified) AS modified,
            SUM(accrued) AS accrued
        FROM accrued
        LEFT JOIN office ON
            accrued.office = office.office
        WHERE
            year = {} AND
            accrued.office = '{}'
            {}
            {}
        GROUP BY year, accrued.office, month
        ORDER BY year, accrued.office, month
    """
    stmt = stmt.format(year, office, opt_line, class_line)
    conn = sqlite3.connect(DBNAME)
    data = pd.read_sql(stmt, conn).round(2)
    conn.close()
    if cum:
        for key in ['approved', 'modified', 'accrued']:
            data[key] = data[key].cumsum()
    return data

def make_table():
    data = get_data(YEAR, OFFICE)
    columns = [{'name': COLNAMES[col], 'id': col} for col in data.columns]
    """
    for i, col in enumerate(columns):
        if col['name'] in MOMENTS.values():
            columns[i]['type'] = 'numeric'
            columns[i]['format'] = Format(group=',')
    """
    return html.Div([
        dash_table.DataTable(
            id = 'accrued_table',
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

def generate_figure(df):
    months = ['ENE', 'FEB', 'MAR', 'ABR', 'MAY', 'JUN', 'JUL', 'AGO', 'SEP', 'OCT', 'NOV', 'DIC']
    data = df.groupby('month').sum() / 1e6
    data = data.reset_index()
    data['month'] = data['month'].apply(lambda x: months[x - 1])
    fig = {
        'data': [
                go.Scatter(name='Aprobado', x=data['month'], y=data['approved']),
                go.Scatter(name='Modificado', x=data['month'], y=data['modified']),
                go.Scatter(name='Devengado', x=data['month'], y=data['accrued'], fill='tozeroy'),
            ],
        'layout' : go.Layout(
            xaxis = {
                'title': 'Meses',
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
            id = 'accrued_plot',
            figure = generate_figure(get_data(YEAR, OFFICE)),
        )
    ])

def make_check_details():
    return dcc.Checklist(
        id = 'cumsum_control',
        options = [
            {
                'label': 'Acumulado',
                'value': 0
            }
        ],
        value=[],
    )

def make_year_control():
    years = get_years()
    control = html.Div([
        html.Label('Ejercicios fiscales'),
        dcc.Dropdown(
            id = 'object_year_control',
            options = [
                {
                    'label': year,
                    'value': year,
                } for i, year in enumerate(years)
            ],
            value = years[-1],
        )
    ])
    return control

def make_office_control():
    offices = get_offices().to_dict('records')
    control = html.Div([
        html.Label('Oficinas'),
        dcc.Dropdown(
            id = 'object_office_control',
            options = [
                {
                    'label': '{} - {}'.format(rec['office'], rec['office_name']),
                    'value': rec['office']
                } for i, rec in enumerate(offices)
            ],
            value = offices[0]['office'],
        )
    ])
    return control

def make_structure_control():
    structure = get_structure(YEAR, OFFICE).to_dict('records')
    control = html.Div([
        html.Label('Unidades/Líneas'),
        dcc.Dropdown(
            id = 'object_structure_control',
            options = [
                {
                    'label': '{} - {}'.format(rec['est'], rec['est_name']),
                    'value': rec['est']
                } for i, rec in enumerate(structure)
            ]
        )
    ])
    return control

def make_object_control():
    conn = sqlite3.connect('data/budget.db')
    stmt = "SELECT object, object_name FROM object WHERE object >= '5'"
    objects = pd.read_sql(stmt, conn)
    conn.close()
    control = html.Div([
        html.Label('Clasificador presupuestario (rubro, cuenta o especifico)'),
        dcc.Dropdown(
            id = 'object_classifier',
            options = [
                {
                    'label': item[1].object + ' - ' + item[1].object_name,
                    'value': objects.iloc[item[0]]['object']
                } for item in objects.iterrows()
            ],
        )
    ])
    return control


txt_header = '''
# Monitor presupuestario
'''

txt_by_object = '''
Este dashboard permite revisar la ejecución presupuestaria mensual
dentro de cada ejercicio fiscal para una determinada unidad
administrativa o clasificador de egreso.
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
            dbc.Row(dbc.Col([
                make_year_control(),
            ])),
            dbc.Row(dbc.Col([
                make_office_control(),
            ])),
            dbc.Row(dbc.Col([
                make_structure_control(),
            ])),
            dbc.Row(dbc.Col([
                make_object_control(),
            ])),
        ], md=4),
        dbc.Col(
            dbc.Tabs([
                dbc.Tab([
                    dbc.Row(dbc.Col([
                        make_check_details(),
                    ])),
                    dbc.Row(dbc.Col([
                        make_figure()
                    ])),
                ], label='Gráfica', tab_id='plot'),
                dbc.Tab([
                    dbc.Row(dbc.Col([
                        html.A(
                            'Descargar CSV',
                            # href='static/budget_by_object.csv',
                            download='budget.csv',
                            id='accrued_csv',
                            className='btn btn-primary'
                        ),
                        ' ',
                        html.A(
                            'Descargar XLS',
                            # href='static/budget_by_object.xlsx',
                            download='budget.xlsx',
                            id='accrued_xlsx',
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
    [
        Output(component_id='accrued_table', component_property='data'),
        Output(component_id='accrued_plot', component_property='figure'),

    ],
    [
        Input(component_id='object_year_control', component_property='value'),
        Input(component_id='object_office_control', component_property='value'),
        Input(component_id='object_structure_control', component_property='value'),
        Input(component_id='object_classifier', component_property='value'),
        Input(component_id='cumsum_control', component_property='value'),
    ]
)
def update_tabs(year, office, est, classifier, accum):
    YEAR = year
    OFFICE = office
    data = get_data(YEAR, OFFICE, line=est, classifier=classifier, 
        cum = True if len(accum) > 0 else False)
    fig = generate_figure(data)
    return data.to_dict('records'), fig
   
@app.callback(
    Output(component_id='object_structure_control', component_property='options'),
    [
        Input(component_id='object_year_control', component_property='value'),
        Input(component_id='object_office_control', component_property='value'),
    ]
)
def update_structure(year, office):
    structure = get_structure(year, office).to_dict('records')
    options = [
                {
                    'label': '{} - {}'.format(rec['est'], rec['est_name']),
                    'value': rec['est']
                } for i, rec in enumerate(structure)
    ]
    return options

@app.callback(
    Output(component_id='accrued_csv', component_property='href'),
    [
        Input(component_id='accrued_table', component_property='data'),
    ]
)
def download_csv(data):
    df = pd.DataFrame(data)
    csv_string = df.to_csv(index=False)
    csv_string = 'data:text/csv;charset=utf-8,' + urllib.parse.quote(csv_string)
    return csv_string

@app.callback(
    Output(component_id='accrued_xlsx', component_property='href'),
    [
        Input(component_id='accrued_table', component_property='data'),
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
