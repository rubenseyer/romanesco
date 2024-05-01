import psycopg


class XdbPostgresql:
    type: str = 'postgresql'
    db: psycopg.Connection

    def __init__(self, connection_str: str):
        self.db = psycopg.connect(connection_str, autocommit=True)

    def transaction(self):
        return self.db.transaction()

    def cursor(self):
        return self.db.cursor()

    def close(self):
        return self.db.close()


# Dirty patching to support ? params ....
from psycopg._queries import PostgresQuery

def _patch_convert(func):
    def _convert(self, query, vars):
        if isinstance(query, str):
            query = query.replace('?', '%s')
        return func(self, query, vars)
    return _convert

PostgresQuery.convert = _patch_convert(PostgresQuery.convert)
