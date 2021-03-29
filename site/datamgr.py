import sqlite3
import pandas as pd

class AnnualBudget:
    dbname = 'data/budget.db'
    moments = {
        'PL': '1. Preliminar',
        'PR': '2. Propuesto',
        'AP': '3. Aprobado',
        'MD': '4. Modificado',
        'DV': '5. Devengado'
    }
    index_short = ['year', 'office', 'office_name', 'level', 'object', 'moment']
    def __init__(self):
        self.obj = ''
        self.office = ''
        self.details = None
        self.df_annual_budget = None
        self.cache_years = None
        self.cache_objects = None
    def query(self, obj='', office='', details=False, use_cache=True):
        # Checking cache correspondence
        if use_cache and self.obj == obj and self.office == office and self.details == details:
            print("Annual Budget Query: using cache...") 
            return self.df_annual_budget
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
        conn = sqlite3.connect(self.dbname)
        data = pd.read_sql(stmt, conn)
        conn.close()

        # Check if data were returned
        print("Annual Budget Query: adapting the dataframe...") 
        if len(data) == 0:
            return None
        # Changing labels for 'moment' and 'level' attributes
        labels = data['moment'].unique()
        colnames = [self.moments[label] for label in labels]
        data['moment'].replace(labels, colnames, inplace=True)
        data['level'].replace(
            ['CG', 'DE'],
            ['Gobierno central', 'Descentralizadas'],
            inplace=True
        )
        data.set_index(self.index_large if details else self.index_short, inplace=True)
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
        # Making a cache
        self.obj = obj 
        self.office = office
        self.details = details 
        self.df_annual_budget = df
        print("Annual Budget Query: returning the dataframe") 
        return df
    def years(self, use_cache=True):
        if use_cache and self.cache_years != None:
            return self.cache_years
        stmt = 'SELECT DISTINCT(year) FROM budget ORDER BY year'
        conn = sqlite3.connect(self.dbname)
        c = conn.cursor()
        years = [year[0] for year in c.execute(stmt)] 
        conn.close()
        self.cache_years = years;
        return years
    def objects(self, use_cache=True):
        if use_cache and self.cache_objects != None:
            return self.cache_objects 
        stmt = """
            SELECT A.object, object_name FROM 
                (
                    SELECT DISTINCT(SUBSTR(object, 1, 2)) AS object FROM budget
                    UNION
                    SELECT DISTINCT(SUBSTR(object, 1, 3)) AS object FROM budget
                    UNION
                    SELECT DISTINCT(SUBSTR(object, 1, 5)) AS object FROM budget
                ) AS A
            LEFT JOIN object 
                ON A.object = object.object
            ORDER BY A.object
        """       
        conn = sqlite3.connect(self.dbname)
        c = conn.cursor()
        objs = [
            {
                'object': obj[0], 
                'object_name': obj[1] if obj[1] != None else ""
            }
            for obj in c.execute(stmt)
        ] 
        conn.close()
        self.cache_objects = objs
        return objs

class MonthlyBudget:
    dbname = "data/master.db"
    def __init__(self):
        self.year = ''
        self.office = ''
        self.program = ''
        self.obj = ''
        self.cache_years = None
        self.cache_offices = ''
        self.cache_programs = ''
        self.cache_objects = ''
        self.cache_monthly_budget = None
    def query(self, year='', office='', program='', obj='', use_cache=True):
        if use_cache and self.year == year and self.office == office and self.progam == program and self.obj == obj:
            print("Monthly Budget Query: using cache...")
            return self.cache_monthly_budget
        stmt_program = f"  AND program LIKE '{program}%' " \
            if program != '' \
            else ''
        grp_program = " program," if program != '' else ''
        grp_object = " object," if obj != '' else ''
        stmt_object = f" AND object LIKE '{obj}%' " \
            if obj != '' \
            else ''
        stmt = f"""
            SELECT
                month,
                IFNULL(approved, 0) AS approved,
                IFNULL(modified, 0) AS modified,
                IFNULL(accrued, 0) AS accrued
            FROM (
                SELECT * FROM (
                    WITH RECURSIVE cnt(x) AS
                    (SELECT 1 UNION SELECT x + 1 FROM cnt LIMIT 12)
                    SELECT x AS month FROM cnt
                ) AS m
                LEFT JOIN (
                    SELECT
                        month,
                        SUM(approved) AS approved,
                        SUM(modified) AS modified,
                        SUM(accrued) AS accrued
                    FROM accrued
                    WHERE
                        year = '{year}' AND
                        office = '{office}'
                        {stmt_program}
                        {stmt_object}
                    GROUP BY month
                    ORDER BY month
                ) AS accrued
                ON m.month = accrued.month
            )
        """
        conn = sqlite3.connect(self.dbname)
        c = conn.cursor()
        data = [
            {
                'month': el[0],
                'approved': el[1],
                'modified': el[2],
                'accrued': el[3]
            }
            for el in c.execute(stmt)
        ]
        conn.close()
        self.cache_monthly_budget = data
        return data
    def years(self, use_cache=True):
        if use_cache and self.cache_years != None:
            return self.cache_years 
        stmt = 'SELECT DISTINCT(year) FROM accrued ORDER BY year'
        conn = sqlite3.connect(self.dbname)
        c = conn.cursor()
        years = [{'id': year[0], 'name': year[0]} for year in c.execute(stmt)] 
        conn.close()
        self.cache_years = years;
        return years
    def offices(self, year='', use_cache=True):
        if use_cache and year == self.year and cache_offices != None:
            return cache_offices
        if year != '':
            stmt_year = f"WHERE year='{year}'"
        else:
            stmt_year = ""
        stmt = f"""
            SELECT accrued.office, office_name
            FROM accrued
            LEFT JOIN office ON
                accrued.office=office.office
            {stmt_year}
            GROUP BY accrued.office
            ORDER BY accrued.office
        """
        conn = sqlite3.connect(self.dbname)
        c = conn.cursor()
        offices = [{'id': el[0], 'name': el[1]} for el in c.execute(stmt)]
        conn.close()
        self.cache_offices = offices
        return offices
    def programs(self, year='', office='', use_cache=True):
        if year=='' or office=='':
            return []
        if use_cache and self.cache_programs != None and year == self.year and office == self.office:
            return self.cache_programs
        stmt = f"""
           SELECT A.program, program_name FROM 
                (
                    SELECT DISTINCT(SUBSTR(program, 1, 2)) AS program FROM accrued
                        WHERE year='{year}' AND office='{office}'
                    UNION
                    SELECT DISTINCT(SUBSTR(program, 1, 4)) AS program FROM accrued
                        WHERE year='{year}' AND office='{office}'
                ) AS A
            LEFT JOIN program 
                ON A.program = program.program AND
                   program.year = '{year}' AND
                   program.office = '{office}'
            ORDER BY A.program
        """
        # print("Monthly Budget: SQL statement...")
        # print(stmt)
        conn = sqlite3.connect(self.dbname)
        c = conn.cursor()
        programs = [
            {
                'id': el[0],
                'name': el[1]
            }
            for el in c.execute(stmt)
        ]
        conn.close()
        self.cache_programs = programs
        return programs
    def objects(self, year='', office='', use_cache=True):
        if year=='' or office=='':
            return []
        if use_cache and self.cache_objects != None and year == self.year and office == self.office:
            return self.cache_objects
        stmt = f"""
            SELECT A.object, object_name FROM 
                (
                    SELECT DISTINCT(SUBSTR(object, 1, 2)) AS object FROM accrued
                        WHERE year='{year}' AND office='{office}'
                    UNION
                    SELECT DISTINCT(SUBSTR(object, 1, 3)) AS object FROM accrued
                        WHERE year='{year}' AND office='{office}'
                    UNION
                    SELECT DISTINCT(SUBSTR(object, 1, 5)) AS object FROM accrued
                        WHERE year='{year}' AND office='{office}'
                ) AS A
            LEFT JOIN object 
                ON A.object = object.object
            ORDER BY A.object
        """
        conn = sqlite3.connect(self.dbname)
        c = conn.cursor()
        objects = [
            {
                'id': el[0],
                'name': el[1]
            }
            for el in c.execute(stmt)
        ]
        conn.close()
        self.cache_objects = objects
        return objects
 
if __name__ == "__main__":
    mb = MonthlyBudget()
    print(mb.query('2015', '0200', '01', '511'))
