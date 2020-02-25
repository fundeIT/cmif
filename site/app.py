import re
from datetime import datetime
import dash
import dash_bootstrap_components as dbc
from flask import Flask, request, make_response
from flask_restful import Resource, Api, reqparse
import queries

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

@server.before_request
def before_request():
    """
    Get information from every request taking date and time, url requested,
    as well as language, platform, and browser of the client.
    This information is appended to a log file.
    """
    # Saving request data to log.txt
    if len(re.findall('^/_|^/assets', request.path)) == 0:
        now = datetime.now()
        current_month = now.strftime("%Y%02m")
        logfile = './log/' + current_month
        f = open(logfile, 'a')
        attrs = str(now).split() + [
            request.remote_addr,
            request.path,
            str(request.accept_languages),
            request.user_agent.platform,
            request.user_agent.browser,
        ]
        f.write('|'.join(attrs) + '\n')
        f.close()


api = Api(server)
parser = reqparse.RequestParser()
parser.add_argument('year', type=int, default=2020, help='Fiscal year')
parser.add_argument('struct', type=int, default=0, help='Include budgetary structure')
parser.add_argument('source', type=int, default=0, help='Funding source')
parser.add_argument('code_len', type=int, default=0, help='Type of budgetary code')

class apiOffices(Resource):
    def get(self):
        data = queries.offices()
        output = make_response(data.to_csv(index=False))
        output.headers["Content-Disposition"] = "attachment; filename=offices_export.csv"
        output.headers["Content-type"] = "text/csv"
        return output

class apiBudgetaryCodes(Resource):
    def get(self):
        data = queries.budgetary_codes()
        output = make_response(data.to_csv(index=False))
        output.headers["Content-Disposition"] = "attachment; filename=budgetary_codes_export.csv"
        output.headers["Content-type"] = "text/csv"
        return output

class apiYearlyBudget(Resource):
    def get(self):
        args = parser.parse_args()
        data = queries.annual_budget(args['year'], args['struct'], args['source'], args['code_len'])
        if not data.empty:
            output = make_response(data.to_csv(index=False))
            output.headers["Content-Disposition"] = "attachment; filename=budget_export.csv"
            output.headers["Content-type"] = "text/csv"
        else:
            output = make_response("With parameters given, data is not available.")
            output.headers["Content-type"] = "text/text"
        return output

api.add_resource(apiYearlyBudget, '/api/v1/budget')
api.add_resource(apiOffices, '/api/v1/offices')
api.add_resource(apiBudgetaryCodes, '/api/v1/budgetary_codes')
