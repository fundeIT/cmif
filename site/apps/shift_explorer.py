import io
import base64
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
import geopandas
import matplotlib.pyplot as plt

from app import app
import queries as qry

DBNAME = 'data/master.db'

def get_data(year, month=None):
    conn = sqlite3.connect(DBNAME)
    option = ''
    if month:
        option = f"month = {month} AND "
    stmt = f"""
        SELECT
            office, unit, line, source,
            SUBSTR(object, 0, 3) AS head,
            SUBSTR(object, 0, 4) AS subhead,
            object,
            SUM(modified - approved) AS shifted
        FROM accrued
        WHERE
            year={year} AND
            {option}
            SUBSTR(office, 3, 2) = '00'
        GROUP BY office, unit, line, source, head, subhead, object
        ORDER BY office, unit, line, source, head, subhead, object
    """
    data = pd.read_sql(stmt, conn)
    conn.close()
    return data

MONTHS = {
    1 : 'ENE', 2 : 'FEB', 3 : 'MAR',
    4 : 'ABR', 5 : 'MAY', 6 : 'JUN',
    7 : 'JUL', 8 : 'AGO', 9 : 'SEP',
    10 : 'OCT', 11 : 'NOV', 12 : 'DIC'
}

# Getting valid periods
def get_periods():
    conn = sqlite3.connect(DBNAME)
    stmt_years = """
        SELECT DISTINCT(year)
        FROM accrued
        ORDER BY year
    """
    stmt_months = """
        SELECT DISTINCT(month)
        FROM accrued
        WHERE year={}
        ORDER BY month
    """
    y = conn.cursor()
    m = conn.cursor()
    periods = {
        year[0] : [
            month[0] for month in m.execute(stmt_months.format(year[0]))
        ]
        for year in y.execute(stmt_years)
    }
    conn.close()
    return periods

periods = get_periods()
year = list(periods.keys())[-1]
data = get_data(year)

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
    conn = sqlite3.connect(DBNAME)
    data = pd.read_sql(stmt, conn)
    conn.close()
    return data

periods = get_periods()
year = list(periods.keys())[-1]
data = get_data(year)
offices = qry.get_offices(year)
structure = get_structure(year, '0100')

def make_year_control():
    years = list(periods.keys())
    control = html.Div([
        html.Label('Año'),
        dcc.Dropdown(
            id = 'year_control',
            options = [
                {
                    'label': key,
                    'value': key,
                } for key in years
            ],
			value=years[-1],
            clearable = False
        )
    ])
    return control

def make_month_control():
    control = html.Div([
        html.Label('Mes'),
        dcc.Dropdown(
            id='month_control',
            options = [
                {
                    'label': MONTHS[month],
                    'value': month
                } for month in periods[year]
            ]
        )
    ])
    return control

def make_office_control():
    offices = qry.get_offices(year).to_dict('records')
    control = html.Div([
        html.Label('Oficinas'),
        dcc.Dropdown(
            id = 'office_control',
            options = [
                {
                    'label': '{} - {}'.format(rec['office'], rec['office_name']),
                    'value': rec['office']
                } for i, rec in enumerate(offices)
            ],
            disabled = False,
        )
    ])
    return control

def make_structure_control():
    control = html.Div([
        html.Label('Unidades/Líneas'),
        dcc.Dropdown(
            id = 'structure_control',
            options = [
                {
                    'label': '{} - {}'.format(rec['est'], rec['est_name']),
                    'value': rec['est']
                } for i, rec in enumerate(structure.to_dict('records'))
            ],
            disabled = True,
        )
    ])
    return control

def make_detail_control():
    control = html.Div([
        html.Label('Nivel de detalle'),
        dcc.Dropdown(
            id = 'detail_control',
            options = [
                {'label': 'Rubro', 'value': 2},
                {'label': 'Cuenta', 'value': 3},
                {'label': 'Objeto específico', 'value': 5},
            ],
        )
    ])
    return control

def prepare_figure(df):
    source = []
    target = []
    value = []
    label = []
    color = []
    keys = ['global'] + list(df.columns[:-1])
    df['global'] = df['shifted'].apply(lambda val: 'in' if val >= 0 else 'out')
    if 'office' in df.columns:
        df['office'] = df['office'].apply(
            lambda s: qry.get_office_name(s, offices) 
        ) 
    for i in range(0, len(keys) - 1):
        subset = df.groupby(keys[0:i + 2])['shifted'].sum().reset_index()
        subset = subset[subset['shifted'] != 0]
        for row in subset.iterrows():
            record = row[1].to_dict()
            source_label = '-'.join([record[key] for key in list(record.keys())[1:-2]])
            target_label = '-'.join([record[key] for key in list(record.keys())[1:-1]])
            if record['shifted'] < 0:
                source_label, target_label = target_label, source_label
                color.append('rgba(255, 0, 0, 0.4)')
            else:
                color.append('rgba(0, 255, 0, 0.4)')
            """
            if source_label == '':
                source_label = 'A'
            if target_label == '':
                target_label = 'B'
            """
            if not source_label in label:
                label.append(source_label)
            source_index = label.index(source_label)
            if not target_label in label:
                label.append(target_label)
            target_index = label.index(target_label)
            source.append(source_index)
            target.append(target_index)
            value.append(abs(record['shifted']))
    fig = {
        'data': [
                go.Sankey(
                    link = dict(
                        source = source,
                        target = target,
                        value = value,
                        color = color
                    ),
                    node = dict(
                        label = label,
                        color = 'blue'
                    )
                ),
            ],
        'layout': go.Layout(
            font_size = 6,
        )
    }
    return fig

def make_figure():
    df = data.groupby('office')['shifted'].sum().reset_index()
    return html.Div([
        dcc.Graph(
            id = 'shifted_figure',
            figure = prepare_figure(df),
            config = {
                'displaylogo': False,
            },
        )
    ])


def make_table(df=None):
    if not df:
        df = data.groupby('office')['shifted'].sum().reset_index()
    df = df.round(2)
    columns = [{'name': col, 'id': col} for col in df.columns]
    return html.Div([
        dash_table.DataTable(
            id = 'shifted_table',
            columns = columns,
            data = df.to_dict('records'),
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

txt_header = '''
# Modificaciones presupuestarias
'''

txt_intro = '''
Esta herramienta permite revisar los cambios hechos en el presupuesto de un determinado período.
'''

content = dbc.Container([
    dbc.Row([
        dbc.Col(dcc.Markdown(txt_header))
    ]),
    dbc.Row([
        dbc.Col([
            dcc.Markdown(txt_intro),
            make_year_control(),
            make_month_control(),
            make_office_control(),
            make_structure_control(),
            make_detail_control(),
        ], md=4),
        dbc.Col(
            dbc.Tabs([
                dbc.Tab([
                    make_figure(),
                    html.A(
                        'Descargar CSV',
                        # href='static/budget_by_object.csv',
                        download='budget.csv',
                        id='download_csv_shifts',
                        className='btn btn-primary'
                    ),
                ], label='Gráficas', tab_id='yearly'),
                dbc.Tab([
                    make_table(),
                ], label='Tabla', tab_id='map'),
            ], id='tabs'),
        ),
    ]),
])

layout = html.Div([content,])

@app.callback(
    [
        Output(component_id='month_control', component_property='options'),
        Output(component_id='office_control', component_property='options'),
    ],
    [
        Input(component_id='year_control', component_property='value'),
    ]
)
def update_months(tmp_year):
    year = tmp_year
    month_options = options = [
        {
            'label': MONTHS[month],
            'value': month
        } for month in periods[year]
    ]
    offices = qry.get_offices(year).to_dict('records')
    offices_options = [
        {
            'label': '{} - {}'.format(rec['office'], rec['office_name']),
            'value': rec['office']
        } for i, rec in enumerate(offices)
    ]
    return month_options, offices_options

@app.callback(
    [
        Output(component_id='structure_control', component_property='disabled'),
        Output(component_id='structure_control', component_property='options'),
    ],
    [
        Input(component_id='office_control', component_property='value'),
    ]
)
def update_structure(office):
    disabled = True
    if office:
        disabled = False
    if not disabled:
        structure = get_structure(year, office).to_dict('records')
    else:
        structure = get_structure(year, '0100').to_dict('records')
    options = [
        {
            'label': '{} - {}'.format(rec['est'], rec['est_name']),
            'value': rec['est']
        } for i, rec in enumerate(structure)
    ]
    return disabled, options

@app.callback(
    [
        Output(component_id='download_csv_shifts', component_property='href'),
        Output(component_id='shifted_figure', component_property='figure'),
        Output(component_id='shifted_table', component_property='data'),
        Output(component_id='shifted_table', component_property='columns'),
    ],
    [
        Input(component_id='year_control', component_property='value'),
        Input(component_id='month_control', component_property='value'),
        Input(component_id='office_control', component_property='value'),
        Input(component_id='structure_control', component_property='value'),
        Input(component_id='detail_control', component_property='value'),
    ]
)
def update_download(year, month, office, structure, detail):
    data = get_data(year, month)
    group = []
    if not office and not detail:
        group.append('office')
    if office:
        data = data[data['office'] == office]
    if structure:
        if len(structure) == 2:
            group.append('unit')
            data = data[data['unit'] == structure]
        else:
            group.append('line')
            data = data[data['line'] == structure]
    else:
        if office:
            group.append('unit')
    if detail:
        data['object'] = data['object'].apply(lambda s: s[:detail])
        group.append('object')
    data = data.groupby(group)['shifted'].sum().reset_index()
    fig = prepare_figure(data)
    csv_string = data.to_csv(index=False)
    csv_string = 'data:text/csv;charset=utf-8,' + urllib.parse.quote(csv_string)
    data = data[data.shifted != 0].round(2)
    columns = [{'name': col, 'id': col} for col in data.columns]
    return csv_string, fig, data.to_dict('records'), columns
