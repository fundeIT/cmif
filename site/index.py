#!/usr/bin/env python

import sys
import getopt
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output
from tornado.wsgi import WSGIContainer
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop
from tornado.web import FallbackHandler, RequestHandler, Application, \
                        StaticFileHandler

from app import app
from apps import budget_explorer, budget_monitor

navbar = dbc.NavbarSimple(
    children=[
        dbc.NavItem(dbc.NavLink("Inicio", href="/")),
        dbc.DropdownMenu(
            nav=True,
            in_navbar=True,
            label="Menu",
            children=[
                dbc.DropdownMenuItem(html.A("Explorador de presupuestos", 
                    href='/budget_explorer')),
                dbc.DropdownMenuItem(html.A("Monitor presupuestario",
                    href='/budget_monitor')),
                dbc.DropdownMenuItem(divider=True),
                dbc.DropdownMenuItem("Otros..."),
            ],
        ),
    ],
    brand="FUNDE | Centro de Monitoreo e Incidencia Fiscal",
    brand_href="#",
    sticky="top",
    className='bg-success',
)

app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    navbar,
    html.Div(id='page-content'),
])


main_text = '''
FUNDE está ejecutando el proyecto “Monitoreo ciudadano de la transparencia
fiscal en El Salvador”. Este proyecto contribuirá a la transparencia fiscal y
la lucha contra la corrupción a través del uso intensivo de bases de datos y de
aplicaciones informáticas.  Consiste en un **observatorio ciudadano**, denominado
Centro de Monitoreo e Incidencia Fiscal, que dará seguimiento al presupuesto
general del Estado, orientado hacia la promoción del acceso, uso y análisis de
información sobre las finanzas públicas, en formatos que sean asequibles, de fácil acceso y
comprensibles para la población en general.


Este sitio estará compuesto por aplicaciones o **dashboards**, por medio de los cuales
los usuarios podrán hacer consultas, visualizar gráficas interactivas,
ordenar o filtrar los resultados y descargar los datos. Inicialmente se presenta
el dashboard [Explorador de presupuestos](/budget_explorer), para consultar presupuestos desde el
año 2012. Más adelante se agregarán nuevos dashboards sobre ingresos,
transferencias presupuestarias, proyectos de inversión, deuda pública y otros
tópicos.


Además, con el apoyo de los dashboards, se elaborarán **artículos de análisis**
sobre diferentes aspectos de las finanzas públicas en El Salvador, para explicar
o comprender las decisiones fiscales, su efecto en las políticas públicas y su
potencial impacto en el bienestar de la población. Estos artículos ayudarán a
dar sentido y carácter humano a las tradicionalmente frías cifras financieras.
'''

budget_explorer_text = '''
Este [dashboard](/budget_explorer) permite consultar la evolución de los presupuestos de las instituciones
públicas según los clasificadores de egresos. Contiene datos desde el año 2012
para diferentes momentos: cuando los presupuestos son propuestos a la Asamblea Legislativa,
cuando son aprobados por los diputados, cuando son modificados durante el ejercicio fiscal y,
finalmente, cuando han sido ejecutados (devengados).
'''

default_content = html.Div([
    dbc.Container([
        dbc.Row([
            dbc.Col(html.H1('Centro de Monitoreo e Incidencia Fiscal')),
        ]),
        dbc.Row([
            dbc.Col(dcc.Markdown(main_text), md=8),
            dbc.Col(html.Img(src='assets/icons/plot.svg', width='120px')),
        ]),
        dbc.Row([
            dbc.Col(html.H2('Explorador de presupuestos')),
        ]),
        dbc.Row([
            dbc.Col([
                dcc.Markdown(budget_explorer_text),
                html.A('Entrar', href='/budget_explorer', className='btn btn-primary'),
            ], md=8),
            dbc.Col(html.A(html.Img(src='assets/icons/budget.svg', width='120px'), href='/budget_explorer')),
        ]),
    ]),
])


@app.callback(Output('page-content', 'children'),
              [Input('url', 'pathname')])
def display_page(pathname):
    if pathname == '/':
        return default_content 
    elif pathname == '/budget_explorer':
        return budget_explorer.layout
    elif pathname == '/budget_monitor':
        return budget_monitor.layout
    else:
        return '404'

tr = WSGIContainer(app.server)
application = Application([
    (r"/static/(.*)", StaticFileHandler, {'path': 'static'}),
    (r".*", FallbackHandler, dict(fallback=tr)),
])

if __name__ == '__main__':
    try:
        opts, args = getopt.getopt(sys.argv[1:], "sdp:", ["secure", "debug", "port"])
    except getopt.GetoptError as err:
        print(str(err))
        sys.exit(2)
    debug = False
    secure = False
    port = 8050
    for o, a in opts:
        if o in ["-d", "--debug"]:
            debug = True
        elif o in ("-p", "--port"):
            port = int(a)
        elif o in ('-s', '--secure'):
            secure = True
        else:
            assert False, "unhandled option"
    DEBUG = debug
    if debug:
        app.run_server(port=port, host='0.0.0.0', debug=True)
    else:
        if secure:
            http_server = HTTPServer(application, ssl_options={
                "certfile": '',
                "keyfile": '',
            })
            port = 443
        else:
            http_server = HTTPServer(application)
            port = 80
        http_server.listen(port)
        IOLoop.instance().start()
