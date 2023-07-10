

_db_providers = {}

try:
    from .sqlite import XdbSqlite
    _db_providers['sqlite'] = XdbSqlite
except:
    pass

try:
    from .postgresql import XdbPostgresql
    _db_providers['postgresql'] = XdbPostgresql
except:
    pass


def connect_db(connection_str: str):
    db_type = connection_str.split(':')[0]
    provider = _db_providers.get(db_type)
    if provider is None:
        raise ValueError(f'Unsupported database type: {db_type}')
    return provider(connection_str)
