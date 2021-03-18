import sqlite3
import pandas as pd

DBNAME = 'data/budget.db'
MOMENTS = {
    'PL': '1. Preliminar',
    'PR': '2. Propuesto',
    'AP': '3. Aprobado',
    'MD': '4. Modificado',
    'DV': '5. Devengado'
}
INDEX_SHORT = ['year', 'office', 'office_name', 'level', 'object', 'moment']


def annual_budget(obj='', office='', details=False):
    # Optional SQL segment statement for
    # the 'details' condition
    print("Annual Budget Query: preparing statement...") 
    detail_stmt = """
        budget.unit, unit_name, budget.line, line_name, source,
    """ if details else ""
    
    join_stmt = """
    LEFT JOIN unit ON
        budget.year = unit.year AND
        budget.office = unit.office AND
        budget.unit = unit.unit
    LEFT JOIN line ON
        budget.year = line.year AND
        budget.office = line.office AND
        budget.unit = line.unit AND
        budget.line = line.line
    """ if details else ""
    
    # Main SQL query
    stmt = f"""
    SELECT
        budget.year, budget.office AS office, office_name, level, {detail_stmt}
        '{obj}' AS object, moment, ROUND(SUM(amount), 2) AS amount
    FROM budget, office
    {join_stmt}
    WHERE
        object LIKE '{obj}%' AND
        budget.office LIKE '{office}%' AND
        budget.office = office.office
    GROUP BY budget.year, level, budget.office, {detail_stmt} moment
    ORDER BY budget.year, level, budget.office, {detail_stmt} moment
    """
   
    print(stmt)

    print("Annual Budget Query: querying the database...") 
    conn = sqlite3.connect(DBNAME)
    data = pd.read_sql(stmt, conn)
    conn.close()

    # Check if data were returned
    print("Annual Budget Query: adapting the dataframe...") 
    if len(data) == 0:
        return None
    # Changing labels for 'moment' and 'level' attributes
    labels = data['moment'].unique()
    colnames = [MOMENTS[label] for label in labels]
    data['moment'].replace(labels, colnames, inplace=True)
    data['level'].replace(
        ['CG', 'DE'],
        ['Gobierno central', 'Descentralizadas'],
        inplace=True
    )
    data.set_index(INDEX_LARGE if details else INDEX_SHORT, inplace=True)
    df = data.unstack(-1)
    df = df.amount[[item[1] for item in df.columns]]
    df = df.reset_index()
    df.rename(
        columns={
            'year': 'Año',
            'office': 'Oficina',
            'office_name': 'Nombre de la oficina',
            'level': 'Nivel',
            'object': 'Clasificador',
        },
        inplace=True
    )
    if details:
        df.rename(columns={
                'unit': 'Unidad',
                'unit_name': 'Nombre de la unidad',
                'line': 'Línea',
                'line_name': 'Nombre de la línea',
                'source': 'Fuente',
            },
            inplace=True
        )
    print("Annual Budget Query: returning the dataframe") 
    return df

