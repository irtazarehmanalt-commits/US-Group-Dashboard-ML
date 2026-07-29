FORBIDDEN_SQL_KEYWORDS = ['DROP', 'DELETE', 'UPDATE', 'INSERT', 'ALTER', 'CREATE', 'TRUNCATE']

def is_safe_sql(sql: str) -> bool:
    upper_sql = sql.upper()
    return not any(keyword in upper_sql for keyword in FORBIDDEN_SQL_KEYWORDS)