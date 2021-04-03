#!/usr/bin/env python

# This is the main script to run the http server
# (2021) Fundación Nacional para el Desarrollo


# Built-in imports
import sys
import getopt

# Web interface imports
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output

# Server imports
from tornado.wsgi import WSGIContainer
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop
from tornado.web import FallbackHandler, RequestHandler, Application, \
                        StaticFileHandler
# Home-made imports
from app import app
from apps import budget_explorer, stats, tax_explorer
import api

# Secrets & confir import
import trust

# Navigation bar
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
                    href='/app/budget_explorer')),
                dbc.DropdownMenuItem(html.A("Monitor presupuestario",
                    href='/monitor/index.html')),
                dbc.DropdownMenuItem(html.A("Explorador de impuestos",
                    href='/app/tax_explorer')),
            ],
        ),
        dbc.DropdownMenu(
            nav=True,
            in_navbar=True,
            label="Ayuda",
            children=[
                dbc.DropdownMenuItem(html.A("Acerca de", href='/app/about')),
                dbc.DropdownMenuItem(html.A("Estadísticas", href='/app/stats')),
                dbc.DropdownMenuItem(html.A("Código fuente",
                    href='https://github.com/fundeIT/cmif', target='blank')),
            ],
        ),
    ],
)

# Foot page
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



budget_explorer_text = '''
## Explorador de presupuestos

Este [dashboard](/budget_explorer) permite consultar la evolución de los
presupuestos de las instituciones públicas según los clasificadores de egresos.
Contiene datos desde el año 2012 para diferentes momentos: cuando los
presupuestos son propuestos a la Asamblea Legislativa, cuando son aprobados por
los diputados, cuando son modificados durante el ejercicio fiscal y, finalmente,
cuando han sido ejecutados (devengados).
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

def defaultContent():
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
        ]),
    ])
    return default_content

txt_about = open('txt/about.txt', 'r').read()
about = html.Div([
    dbc.Container([
        dbc.Row([
            dbc.Col(html.H1('Centro de Monitoreo e Incidencia Fiscal')),
        ]),
        dbc.Row([
            dbc.Col([
                dcc.Markdown(txt_about),
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
    elif pathname == '/app/tax_explorer':
        return tax_explorer.layout
    elif pathname == "/app/stats":
        return stats.layout
    elif pathname == '/app/about':
        return about
    else:
        return '404'

if __name__ == '__main__':
    try:
        opts, args = getopt.getopt(sys.argv[1:], "sdp:", ["secure", "debug", "port"])
    except getopt.GetoptError as err:
        print(str(err))
        sys.exit(2)
    debug = False
    secure = False
    default_port =True
    port = 5000
    for o, a in opts:
        if o in ["-d", "--debug"]:
            debug = True
        elif o in ('-s', '--secure'):
            secure = True
        elif o in ("-p", "--port"):
            default_port = False
            port = int(a)
        else:
            assert False, "unhandled option"
    # Interface between Dash & Tornado
    # tr = WSGIContainer(app.server)
    # Tornado server
    application = Application([
        # (r"/app/(.*)", FallbackHandler, dict(fallback=tr)),
        (r"/api/(.*)", FallbackHandler, dict(fallback=WSGIContainer(api.app))),
        (r"/(.*)", StaticFileHandler, {'path': 'public', "default_filename": "index.html"}),
    ], debug=debug, autoreload=debug)
    ## if debug:
    ##     app.run_server(port=port, host='0.0.0.0', debug=True)
    if secure:
        http_server = HTTPServer(application, ssl_options={
            "certfile": trust.certfile,
            "keyfile": trust.keypriv,
        })
        if default_port:
            port = 443
    else:
        http_server = HTTPServer(application)
        if default_port:
            port = 80
    http_server.listen(port)
    IOLoop.instance().start()
