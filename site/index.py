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
from apps import budget_explorer, budget_monitor, shift_explorer, stats, tax_explorer

import trust

navbar = dbc.Navbar(
    children = [
        html.A(
            html.Img(src='assets/images/logo_small.png', width='120px'),
            href='/'
        ),
        dbc.DropdownMenu(
            nav=True,
            in_navbar=True,
            label="Tableros",
            children=[
                dbc.DropdownMenuItem(html.A("Explorador de presupuestos",
                    href='/budget_explorer')),
                dbc.DropdownMenuItem(html.A("Monitor presupuestario",
                    href='/budget_monitor')),
                dbc.DropdownMenuItem(html.A("Explorador de impuestos",
                    href='/tax_explorer')),
                dbc.DropdownMenuItem(html.A("Modificaciones presupuestarias",
                    href='/shift_explorer')),
            ],
        ),
        dbc.DropdownMenu(
            nav=True,
            in_navbar=True,
            label="Ayuda",
            children=[
                dbc.DropdownMenuItem(html.A("Acerca de", href='/about')),
                dbc.DropdownMenuItem(html.A("Estadísticas", href='/stats')),
                dbc.DropdownMenuItem(html.A("Código fuente",
                    href='https://github.com/fundeIT/cmif', target='blank')),
            ],
        ),
    ],
)

footer = html.Div([
    dbc.Container([
        dbc.Row([
            dbc.Col(
                html.Img(src='assets/images/funde-ti.png', width='180px'),
                className='text-center'
            ),
            dbc.Col(dcc.Markdown('''
                El Centro de Monitoreo e Incidencia Fiscal (CEMIF) es
                una iniciativa de la
                [Fundación Nacional para el Desarrollo](http://funde.org/),
                capítulo de
                [Transparencia Internacional](https://www.transparency.org/)
                en El Salvador
            ''')),
            dbc.Col(dcc.Markdown('''
                Teléfono +503 2209-5300 |
                Correo electrónico: <funde@funde.org> |
                Calle Arturo Ambrogi No. 411, San Salvador,
                El Salvador C.A.
            ''')),
        ]),
    ]),
])

app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    dbc.Container([
        navbar,
        html.Div(id='page-content'),
        html.Hr(),
        footer,
    ])
])


main_text = '''
FUNDE está ejecutando el proyecto “Monitoreo ciudadano de la transparencia
fiscal en El Salvador”. Este proyecto contribuirá a la transparencia fiscal y la
lucha contra la corrupción a través del uso intensivo de bases de datos y de
aplicaciones informáticas.

El proyecto consiste en un **observatorio ciudadano**, denominado Centro de
Monitoreo e Incidencia Fiscal, que da seguimiento al presupuesto general del
Estado. Está orientado hacia la promoción del acceso, uso y análisis de
información sobre las finanzas públicas, en formatos que sean asequibles, de
fácil acceso y comprensibles para la población en general.

Este sitio está compuesto por aplicaciones o **dashboards**, por medio de los
cuales los usuarios pueden hacer consultas, visualizar gráficas interactivas,
ordenar o filtrar los resultados y descargar los datos.

Además, con el apoyo de los dashboards, se elaborarán **artículos de análisis**
sobre diferentes aspectos de las finanzas públicas en El Salvador, para explicar
o comprender las decisiones fiscales, su efecto en las políticas públicas y su
potencial impacto en el bienestar de la población. Estos artículos ayudarán a
dar sentido y carácter humano a las tradicionalmente frías cifras financieras.
'''

budget_explorer_text = '''
## Explorador de presupuestos

Este [dashboard](/budget_explorer) permite consultar la evolución de los
presupuestos de las instituciones públicas según los clasificadores de egresos.
Contiene datos desde el año 2012 para diferentes momentos: cuando los
presupuestos son propuestos a la Asamblea Legislativa, cuando son aprobados por
los diputados, cuando son modificados durante el ejercicio fiscal y, finalmente,
cuando han sido ejecutados (devengados).
'''

budget_monitor_text = '''
## Monitor presupuestario

Este [dashboard](/budget_moitor) concentra la atención en la ejecución presupuestaria
mes a mes. Permite revisar los montos programados y erogados por cada institución
pública de manera mensual en sus diferentes unidades o códigos de egreso.
'''

tax_explorer_text = '''
## Explorador de impuestos

Las políticas públicas se financian con los impuestos que los ciudadanos(as)
pagan. [Este dashboard](/tax_explorer) permite explorar cómo se ha comportado la
recaudación de impuestos en los últimos años a partir de diferentes criterios:
tipo de sujetos (personas naturales o jurídicas), ubicación geográfica,
actividades económicas o tipo de impuestos. En una gráfica se presenta la
evolución anual y en otra el comportamiento mensual de la recaudación de
impuestos, según los criterios seleccionados.
'''

shift_explorer_text = '''
# Modificaciones presupuestarias (experimental)

En este [dashboard](/shift_explorer) se pueden consultar las modificaciones que
se han realizado en los presupuestos por año y mes. Las modificaciones se
ilustran por medio de flujos que aumentan (verdes) y que disminuyen (rojos). Aún
es un módulo en desarrollo.

'''

default_content = html.Div([
    dbc.Container([
        dbc.Row([
            dbc.Col(
                html.A(
                    html.Img(src='assets/icons/budget.svg', width='120px'),
                    href='/budget_explorer'
                ),
                className='text-center'
            ),
            dbc.Col([
                dcc.Markdown(budget_explorer_text),
                html.A('Entrar', href='/budget_explorer', className='btn btn-primary'),
            ], md=8),
        ]),
        dbc.Row([
            dbc.Col(
                html.A(
                    html.Img(src='assets/icons/plot.svg', width='100px'),
                    href='/budget-monitor'
                ),
                className='text-center'
            ),
            dbc.Col([
                dcc.Markdown(budget_monitor_text),
                html.A('Entrar', href='/budget_monitor', className='btn btn-primary'),
            ], md=8),
        ]),
        dbc.Row([
            dbc.Col(
                html.A(
                    html.Img(src='assets/icons/coins.svg', width='100px'),
                    href='/budget-monitor'
                ),
                className='text-center'
            ),
            dbc.Col([
                dcc.Markdown(tax_explorer_text),
                html.A('Entrar', href='/tax_explorer', className='btn btn-primary'),
            ], md=8),
        ]),
        dbc.Row([
            dbc.Col(
                html.A(
                    html.Img(src='assets/icons/transfer.svg', width='100px'),
                    href='/shit_explorer'
                ),
                className='text-center'
            ),
            dbc.Col([
                dcc.Markdown(shift_explorer_text),
                html.A('Entrar', href='/shift_explorer', className='btn btn-primary'),
            ], md=8),
        ]),

    ]),
])

about = html.Div([
    dbc.Container([
        dbc.Row([
            dbc.Col(html.H1('Centro de Monitoreo e Incidencia Fiscal')),
        ]),
        dbc.Row([
            dbc.Col([
                dcc.Markdown(main_text),
            ]),
        ]),
    ]),
])

@app.callback(Output('page-content', 'children'),
              [Input('url', 'pathname')])
def display_page(pathname):
    if pathname == '/app':
        return default_content
    elif pathname == '/app/budget_explorer':
        return budget_explorer.layout
    elif pathname == '/app/budget_monitor':
        return budget_monitor.layout
    elif pathname == '/app/shift_explorer':
        return shift_explorer.layout
    elif pathname == '/app/tax_explorer':
        return tax_explorer.layout
    elif pathname == "/app/stats":
        return stats.layout
    elif pathname == '/app/about':
        return about
    else:
        return '404'

# Interface between Dash & Tornado

tr = WSGIContainer(app.server)

application = Application([
    (r"/app/(.*)", FallbackHandler, dict(fallback=tr)),
    (r"/(.*)", StaticFileHandler, {'path': 'public', "default_filename": "index.html"}),
])

if __name__ == '__main__':
    try:
        opts, args = getopt.getopt(sys.argv[1:], "sdp:", ["secure", "debug", "port"])
    except getopt.GetoptError as err:
        print(str(err))
        sys.exit(2)
    debug = False
    secure = False
    DEFAULT_PORT = 8050
    port = DEFAULT_PORT
    for o, a in opts:
        if o in ["-d", "--debug"]:
            debug = True
        elif o in ('-s', '--secure'):
            secure = True
        elif o in ("-p", "--port"):
            port = int(a)
        else:
            assert False, "unhandled option"
    if debug:
        app.run_server(port=port, host='0.0.0.0', debug=True)
    else:
        if secure:
            http_server = HTTPServer(application, ssl_options={
                "certfile": trust.certfile,
                "keyfile": trust.keypriv,
            })
            port = 443 if port == DEFAULT_PORT else port
        else:
            http_server = HTTPServer(application)
            port = 80 if port == DEFAULT_PORT else port
        http_server.listen(port)
        IOLoop.instance().start()
