#!/usr/bin/python

import sqlite3
from flask import Flask, request
from flask_restful import Resource, Api

DB = 'data/master.db'

app = Flask(__name__)
api = Api(app)

def query(stmt):
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute(stmt)
    ret = [dict(row) for row in c.fetchall()]
    return ret

class office(Resource):
    def get(self, office_id=None):
        level = request.args.get('level', None)
        if office_id:
            stmt_where = f"WHERE office='{office_id}'"
        else:
            stmt_where = f"WHERE level='{level}'" if level else ""
        stmt = f"""
            SELECT * 
                FROM office 
                {stmt_where}
                ORDER BY level, office
        """
        return query(stmt)

class program(Resource):
    def get(self, office_id=None):
        year = request.args.get('year', None)
        stmt_where = 'WHERE 1'
        if office_id:
            stmt_where += f" AND office='{office_id}'"
        if year:
            stmt_where += f" AND year={year}"
        stmt = f"""
            SELECT * 
                FROM program
                {stmt_where}
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
                # Default level
                stmt_where += " AND office LIKE '__00'"
        if year:
            stmt_where += f" AND year={year}"
        if program:
            stmt_where += f" AND line LIKE '{program}%'"
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


api.add_resource(office, '/api/v1/office', '/api/v1/office/<string:office_id>')
api.add_resource(program, '/api/v1/programs', '/api/v1/programs/<string:office_id>', '/api/v1/office/<string:office_id>/programs')
api.add_resource(budget, '/api/v1/budget', '/api/v1/budget/<string:office_id>', '/api/v1/office/<string:office_id>/budget')

if __name__ == '__main__':
    app.run(debug=True)
