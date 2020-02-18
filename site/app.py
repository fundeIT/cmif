import dash
import dash_bootstrap_components as dbc
from flask import Flask

server = Flask(__name__)

app = dash.Dash(
    __name__,
    server=server,
    external_stylesheets=[
        dbc.themes.BOOTSTRAP,
        'https://fonts.googleapis.com/css?family=Raleway&display=swap',
        'style.css'
    ]
)

app.config.suppress_callback_exceptions = True


app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>FUNDE - Centro de Monitoreo e Incidencia Fiscal</title>
        <meta name="viewport" content="width=device-width, initival-scale=1"/>
        {%favicon%}
        {%css%}
    </head>
    <body>
        <div></div>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
        <div></div>
    </body>
</html>
'''
