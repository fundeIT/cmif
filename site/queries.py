import sqlite3
import pandas as pd

DB = 'data/budget.db'

def offices():
    stmt = "SELECT * FROM office"
    conn = sqlite3.connect(DB)
    data = pd.read_sql(stmt, conn)
    conn.close()
    return data

def budgetary_codes():
    stmt = "SELECT * FROM object"
    conn = sqlite3.connect(DB)
    data = pd.read_sql(stmt, conn)
    conn.close()
    return data

def annual_budget(year, struct=True, source=True, code_len=5):
    q_struct = ' unit, line, ' if struct == 1 else ''
    q_source = ' source, ' if source == 1 else ''
    q_code1 = f" SUBSTR(budget.object, 0, {code_len + 1}) AS code, " \
            if code_len > 0 else ""
    q_code2 = " code, " \
            if code_len > 0 else ""
    stmt = f"""
            SELECT
                    year, budget.office, office_name, {q_struct} {q_source} {q_code1}
                    object_name, moment,
                    SUM(amount) AS amount
            FROM budget
            JOIN office ON
                office.office = budget.office
            JOIN object ON
                object.object = code
            WHERE
                    year={year}
            GROUP BY
                    year, budget.office, {q_struct} {q_source} {q_code2}
                    moment
    """
    conn = sqlite3.connect(DB)
    data = pd.read_sql(stmt, conn)
    index_cols = data.columns[:-1].to_list()
    data = data\
            .set_index(index_cols)\
            .unstack(-1)\
            .fillna(0)['amount']\
            .reset_index()
    data.rename(columns={
            'BG': 'estimated',
            'PR': 'proposed',
            'AP': 'approved',
            'MD': 'modified',
            'DV': 'accrued',
    }, inplace=True)
    conn.close()
    return data
