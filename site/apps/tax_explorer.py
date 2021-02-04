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
import utils

DBNAME = 'data/master.db'

def make_year_control():
    conn = sqlite3.connect(DBNAME)
    stmt = "SELECT DISTINCT(year) FROM tax"
    objects = pd.read_sql(stmt, conn)
    conn.close()
    control = html.Div([
        html.Label('Año'),
        dcc.Dropdown(
            id = 'year_control',
            options = [
                {
                    'label': item[1].year,
                    'value': item[1].year,
                } for item in objects.iterrows()
            ],
			value=objects.iloc[-1]['year'],
        )
    ])
    return control

def make_subject_control():
	control = html.Div([
		html.Label('Sujetos'),
		dcc.Dropdown(
			id='subject_control',
			options=[
				{'label': 'P. Naturales', 'value': 'N'},
				{'label': 'P. Jurídicas', 'value': 'J'},
			],
		)
	])
	return control

def make_department_control():
    conn = sqlite3.connect(DBNAME)
    stmt = """
		SELECT location, location_name
		FROM location
		WHERE location < 100
	"""
    objects = pd.read_sql(stmt, conn)
    conn.close()
    control = html.Div([
        html.Label('Departamento'),
        dcc.Dropdown(
            id = 'department_control',
            options = [
                {
                    'label': item[1].location_name,
                    'value': str(item[1].location).zfill(2),
                } for item in objects.iterrows()
            ],
        )
    ])
    return control

def make_activity_control():
    conn = sqlite3.connect(DBNAME)
    stmt = """
		SELECT activity, activity_name
		FROM activity
	"""
    objects = pd.read_sql(stmt, conn)
    conn.close()
    control = html.Div([
        html.Label('Actividades económicas'),
        dcc.Dropdown(
            id = 'activity_control',
            options = [
                {
                    'label': str(item[1].activity) + ' - ' + item[1].activity_name,
                    'value': item[1].activity,
                } for item in objects.iterrows()
            ],
        )
    ])
    return control

def make_tax_control():
    conn = sqlite3.connect(DBNAME)
    stmt = """
		SELECT tax, tax_name
		FROM tax_class
	"""
    objects = pd.read_sql(stmt, conn)
    conn.close()
    control = html.Div([
        html.Label('Tipos de impuesto'),
        dcc.Dropdown(
            id = 'tax_control',
            options = [
                {
                    'label': str(item[1].tax) + ' - ' + item[1].tax_name,
                    'value': item[1].tax,
                } for item in objects.iterrows()
            ],
        )
    ])
    return control

def prepare_yearly_figure(subject=None, department=None, activity=None, tax=None):
    filters = []
    if subject:
        filters.append(f" subject='{subject}' ")
    if department:
        filters.append(f" department='{department}' ")
    if activity:
        filters.append(f" activity LIKE '{activity}%' ")
    if tax:
        filters.append(f" tax LIKE '{tax}%' ")
    filter = ' AND '.join(filters)
    filter = 'WHERE ' + filter if len(filter) > 0 else ''
    stmt = f"""
        SELECT year, SUM(amount) AS amount
        FROM tax
        {filter}
        GROUP BY year
        ORDER BY year
    """
    conn = sqlite3.connect(DBNAME)
    data = pd.read_sql(stmt, conn)
    conn.close()
    fig = {
        'data': [go.Scatter(x=data['year'], y=data['amount'], fill='tozeroy')],
        'layout' : go.Layout(
            xaxis = {
                'title': 'Ejercicios fiscales',
            },
            yaxis = {
                'title': 'USD',
            },
        ),
    }
    return fig

def make_yearly_figure():
    return html.Div([
        dcc.Graph(
            id = 'yearly_figure',
            figure = prepare_yearly_figure(),
        )
    ])

def prepare_monthly_figure(
    year=None,
    subject=None,
    department=None,
    activity=None,
    tax=None,
    cum=False
):
    filters = []
    if year:
        filters.append(f" year={year} ")
    if subject:
        filters.append(f" subject='{subject}' ")
    if department:
        filters.append(f" department='{department}' ")
    if activity:
        filters.append(f" activity LIKE '{activity}%' ")
    if tax:
        filters.append(f" tax LIKE '{tax}%' ")
    filter = ' AND '.join(filters)
    filter = 'WHERE ' + filter if len(filter) > 0 else ''
    stmt = f"""
        SELECT month, SUM(amount) AS amount
        FROM tax
        {filter}
        GROUP BY month
        ORDER BY month
    """
    conn = sqlite3.connect(DBNAME)
    data = pd.read_sql(stmt, conn)
    conn.close()
    if cum:
        data['amount'] = data['amount'].cumsum()
    data['month'] = data['month'].apply(utils.name_month)
    fig = {
        'data': [go.Scatter(x=data['month'], y=data['amount'], fill='tozeroy')],
        'layout' : go.Layout(
            xaxis = {
                'title': 'Evolución mensual',
            },
            yaxis = {
                'title': 'USD',
            },
        ),
    }
    return fig

def make_monthly_figure():
    return html.Div([
        dcc.Graph(
            id = 'monthly_figure',
            figure = prepare_monthly_figure(),
        )
    ])


def prepare_maps(
    year=None,
    subject=None,
    department=None,
    activity=None,
    tax=None
):
    filters = []
    if year:
        filters.append(f" year={year} ")
    if subject:
        filters.append(f" subject='{subject}' ")
    if department:
        filters.append(f" department='{department}' ")
    if activity:
        filters.append(f" activity LIKE '{activity}%' ")
    if tax:
        filters.append(f" tax LIKE '{tax}%' ")
    filter = ' AND '.join(filters)
    filter = 'WHERE ' + filter if len(filter) > 0 else ''
    stmt = f"""
        SELECT municipality, SUM(amount) AS amount
        FROM tax
        {filter}
        GROUP BY municipality
    """
    conn = sqlite3.connect(DBNAME)
    data = pd.read_sql(stmt, conn)
    conn.close()
    municipality = geopandas.read_file('shp/municipality.shp')
    municipality.rename(columns={'municipali': 'municipality'}, inplace=True)
    if department:
        municipality = municipality[municipality.municipality.apply(lambda s: str(s)[:2]) == department]
    df = municipality.merge(data, on='municipality', how='left').fillna(1e-3)
    fig, ax = plt.subplots()
    df['log'] = df['amount'].apply(np.log10)
    df.plot(
        column='log',
        legend=True,
        cmap='BuGn',
        ax=ax,
        figsize=(16,9),
        legend_kwds={
            'orientation': 'horizontal',
            'label': 'USD (escala $log_{10}$)'
        }
    )
    df.boundary.plot(color='grey', ax=ax, linewidth=0.1)
    plt.title('Impuestos por municipio')
    pic = io.BytesIO()
    plt.savefig(pic, format='png')
    pic.seek(0)
    ret = base64.b64encode(pic.read()).decode('ascii')
    ret = 'data:image/png;base64, ' + ret
    return ret

def make_cumulative():
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

txt_header = '''
# Explorador de impuestos
'''

txt_intro = '''
Esta herramienta permite analizar el comportamiento de los impuestos recaudados
por el Gobierno por períodos de tiempo, tipo de sujetos obligados,
zona geográfica, actividades económicas y tipos de impuesto.

Los datos han sido obtenidos del Portal de Transparencia Fiscal que mantiene
el Ministerio de Hacienda. Actualmente incluye datos desde enero de 2010 hasta
septiembre de 2019 (los datos de 2019 aún están incompletos).
'''

content = dbc.Container([
    dbc.Row([
        dbc.Col(dcc.Markdown(txt_header))
    ]),
    dbc.Row([
        dbc.Col([
            dcc.Markdown(txt_intro),
			make_subject_control(),
			make_department_control(),
            make_activity_control(),
            make_tax_control(),
            make_year_control(),
        ], md=4),
        dbc.Col(
            dbc.Tabs([
                dbc.Tab([
                    html.Br(),
                    html.H5('Evolución anual'),
                    make_yearly_figure(),
                    html.H5('Evolución mensual'),
                    make_monthly_figure(),
                    make_cumulative(),
                ], label='Gráficas', tab_id='yearly'),
            ], id='tabs'),
        ),
    ]),
])

layout = html.Div([content,])

@app.callback(
    [
        Output(component_id='yearly_figure', component_property='figure'),
        Output(component_id='monthly_figure', component_property='figure'),
        # Output(component_id='map_image', component_property='src')
    ],
    [
        Input(component_id='year_control', component_property='value'),
        Input(component_id='subject_control', component_property='value'),
        Input(component_id='department_control', component_property='value'),
        Input(component_id='activity_control', component_property='value'),
        Input(component_id='tax_control', component_property='value'),
        Input(component_id='cumsum_control', component_property='value')
    ]
)
def update(year, subject, department, activity, tax, cumulative):
    yearly_fig = prepare_yearly_figure(subject, department, activity, tax)
    monthly_fig = prepare_monthly_figure(
        year,
        subject,
        department,
        activity,
        tax,
        cum = True if len(cumulative) > 0 else False
    )
    # map = prepare_maps(year, subject, department, activity, tax)
    # return yearly_fig, monthly_fig, map
    return yearly_fig, monthly_fig
