from decimal import Decimal
import apsw
import apsw.ext

import apsw.bestpractice

apsw.bestpractice.apply(apsw.bestpractice.recommended)


class XdbSqlite:
    type: str = 'sqlite'
    db: apsw.Connection

    def __init__(self, connection_str: str):
        # strip the leading 'sqlite://'
        self.db = apsw.Connection(connection_str[9:])

        # adapt the Decimal types
        registrar = apsw.ext.TypesConverterCursorFactory()
        self.db.cursor_factory = registrar
        registrar.register_adapter(Decimal, str)
        registrar.register_converter('decimal_clob', decimal_clob)

        # tracer for debugging
        # def exectracer(cursor, statement, bindings) -> bool:
        #     print(f'SQL on {cursor} stmt {statement.strip()} bindings {bindings}')
        #     return True  # if you return False then execution is aborted
        # self.db.exectrace = exectracer

    def transaction(self):
        # apsw uses the connection itself as context manager for a transaction
        return self.db

    def cursor(self):
        return self.db.cursor()

    def close(self):
        return self.db.close()


def decimal_clob(s: str) -> None | Decimal:
    return Decimal(s) if s is not None else None
