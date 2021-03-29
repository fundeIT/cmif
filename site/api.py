#!/usr/bin/env python

import sqlite3
from flask import Flask, request, send_from_directory
from flask_restful import Resource, Api, reqparse

import datamgr

DB = 'data/master.db'

base_url = '/api/v2'

app = Flask(__name__)

api = Api(app)

parser = reqparse.RequestParser()
parser.add_argument('dict')

def query(stmt):
    print(stmt)
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute(stmt)
    ret = [dict(row) for row in c.fetchall()]
    return ret

class offices(Resource):
    def get(self, office_id=None):
        year = request.args.get('year', None)
        stmt_where = f" AND office.office='{office_id}'" if office_id else ""
        if year:
            stmt = f"""
                SELECT accrued.office, office_name, office.level
                FROM accrued, office 
                WHERE year={year} AND accrued.office=office.office {stmt_where}
                GROUP BY accrued.office
                ORDER BY accrued.office 
            """
        else:
            stmt = f"""
                SELECT * 
                    FROM office 
                    WHERE 1 {stmt_where}
                    ORDER BY level, office
            """
        return query(stmt)

class offices_programs(Resource):
    def get(self, office_id):
        year = request.args.get('year', None)
        stmt_where = 'WHERE 1'
        stmt_where += f" AND office='{office_id}'"
        if year:
            stmt_where += f" AND year={year}"
        stmt = f"""
            SELECT * 
                FROM program
                {stmt_where}
                GROUP BY office, year, program
                ORDER BY office, year, program
        """
        print(stmt)
        return query(stmt)

class budget(Resource):
    def get(self, office_id=None):
        year = request.args.get('year', None)
        program = request.args.get('program', None)
        code = request.args.get('code', None)
        level = request.args.get('level', None)
        accum = request.args.get('accum', None)
        stmt_where = 'WHERE 1'
        if office_id:
            stmt_where += f" AND office='{office_id}'"
        else:
            if level == 'DE':
                stmt_where += " AND office NOT LIKE '__00'"
            else:
                stmt_where += " AND office LIKE '__00'"
        if year:
            stmt_where += f" AND year={year}"
        if program:
            stmt_where += f" AND program LIKE '{program}%'"
        if code:
            stmt_where += f" AND object LIKE'{code}%'"
        stmt = f"""
            SELECT
                year, month,
                SUM(approved) AS approved,
                SUM(modified) AS modified,
                SUM(accrued) AS accrued
            FROM accrued
                {stmt_where}
            GROUP BY year, month 
            ORDER BY year, month 
        """
        return query(stmt)

class years(Resource):
    def get(self, office_id=None):
        stmt_where = f"WHERE office='{office_id}'" if office_id else ""
        stmt = f"""
            SELECT DISTINCT(year)
            FROM accrued
            {stmt_where}
            ORDER BY year
        """
        return query(stmt)
        
class offices_objects(Resource):
    def get(self, office_id):
        year = request.args.get('year', None)
        if not year:
            qry = query(f"""
                SELECT MAX(year) AS year
                FROM accrued
                WHERE office='{office_id}' 
            """)
            year = qry[0]['year'] 
        stmt = f"""
        SELECT object.object, object_name
        FROM object, 
            (
                SELECT object, SUM(modified) AS amount
                FROM accrued
                WHERE year={year} AND office='{office_id}'
                GROUP BY object
            ) AS A
        WHERE INSTR(A.object, object.object) = 1
        GROUP BY object.object
        ORDER BY object.object
        """
        return query(stmt)

class monthly_budget(Resource):
    def get(self, year='', office='', program='', obj=''):
        args = parser.parse_args()
        mb = datamgr.MonthlyBudget()
        if year == '' or args['dict'] == 'year':
            return mb.years()
        elif office == '' or args['dict'] == 'office':
            return mb.offices(year)
        elif args['dict'] == 'program':
            return mb.programs(year, office)
        elif args['dict'] == 'object':
            return mb.objects(year, office)
        else:
            return datamgr.MonthlyBudget().query(year, office, program, obj)

api.add_resource(monthly_budget,
    base_url + '/monthly',
    base_url + '/monthly/<string:year>',
    base_url + '/monthly/<string:year>/<string:office>',
    base_url + '/monthly/<string:year>/<string:office>/<string:program>',
    base_url + '/monthly/<string:year>/<string:office>/<string:program>/<string:obj>',
    base_url + '/monthly/<string:year>/<string:office>/object/<string:obj>'
)

api.add_resource(years,
    base_url + '/years',
    base_url + '/years/<string:office_id>',
    base_url + '/offices/<string:office_id>/years'
)
api.add_resource(offices, 
    base_url + '/offices', 
    base_url + '/offices/<string:office_id>'
)
api.add_resource(offices_programs, 
    base_url + '/offices/<string:office_id>/programs'
)
api.add_resource(offices_objects,
    base_url + '/offices/<string:office_id>/objects'    
)
api.add_resource(budget, 
    base_url + '/budget', 
    base_url + '/budget/<string:office_id>', 
    base_url + '/offices/<string:office_id>/budget')

@app.route('/<path:path>')
def send_js(path):
    return send_from_directory('public', path)

if __name__ == '__main__':
    app.run(debug=True)
