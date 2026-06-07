"""
config/keywords.py
------------------
Authoritative SQL keyword set for MCCU.

Replaces the fragile `keywords.txt` + `keyword_loader.py` pattern from m1.
All keywords are stored here as a Python frozenset — no file I/O required.

The classifier uses SQL_KEYWORDS to determine whether a raw token string is
a keyword or an identifier.  Keywords that the parsers treat as structural
tokens (SELECT, FROM, WHERE, etc.) also have their own TT_* constants in
config/token_types.py.

Source: MySQL 8.0 reserved and non-reserved keywords.
"""

# ---------------------------------------------------------------------------
# Primary keyword set — used for classification during tokenization
# ---------------------------------------------------------------------------

SQL_KEYWORDS: frozenset[str] = frozenset({
    # A
    "ACCESSIBLE", "ADD", "ALL", "ALTER", "ANALYZE", "AND", "AS", "ASC",
    "ASENSITIVE",
    # B
    "BEFORE", "BETWEEN", "BIGINT", "BINARY", "BLOB", "BOTH", "BY",
    # C
    "CALL", "CASCADE", "CASE", "CHANGE", "CHAR", "CHARACTER", "CHECK",
    "COLLATE", "COLUMN", "CONDITION", "CONSTRAINT", "CONTINUE", "CONVERT",
    "CREATE", "CROSS", "CUBE", "CUME_DIST", "CURRENT_DATE", "CURRENT_TIME",
    "CURRENT_TIMESTAMP", "CURRENT_USER", "CURSOR",
    # D
    "DATABASE", "DATABASES", "DAY_HOUR", "DAY_MICROSECOND", "DAY_MINUTE",
    "DAY_SECOND", "DEC", "DECIMAL", "DECLARE", "DEFAULT", "DELAYED",
    "DELETE", "DENSE_RANK", "DESC", "DESCRIBE", "DETERMINISTIC", "DISTINCT",
    "DISTINCTROW", "DIV", "DOUBLE", "DROP", "DUAL",
    # E
    "EACH", "ELSE", "ELSEIF", "EMPTY", "ENCLOSED", "ESCAPED", "EXCEPT",
    "EXISTS", "EXIT", "EXPLAIN", "EXTERNAL",
    # F
    "FALSE", "FETCH", "FIRST_VALUE", "FLOAT", "FLOAT4", "FLOAT8", "FOR",
    "FORCE", "FOREIGN", "FROM", "FULLTEXT", "FUNCTION",
    # G
    "GENERATED", "GET", "GRANT", "GROUP", "GROUPING", "GROUPS",
    # H
    "HAVING", "HIGH_PRIORITY", "HOUR_MICROSECOND", "HOUR_MINUTE",
    "HOUR_SECOND",
    # I
    "IF", "IGNORE", "IN", "INDEX", "INFILE", "INNER", "INOUT",
    "INSENSITIVE", "INSERT", "INT", "INT1", "INT2", "INT3", "INT4", "INT8",
    "INTEGER", "INTERSECT", "INTERVAL", "INTO", "IO_AFTER_GTIDS",
    "IO_BEFORE_GTIDS", "IS", "ITERATE",
    # J
    "JOIN",
    # K
    "KEY", "KEYS", "KILL",
    # L
    "LAG", "LATERAL", "LEAD", "LEADING", "LEAVE", "LEFT", "LIBRARY",
    "LIKE", "LIMIT", "LINEAR", "LINES", "LOAD", "LOCALTIME",
    "LOCALTIMESTAMP", "LOCK", "LONG", "LONGBLOB", "LONGTEXT", "LOOP",
    "LOW_PRIORITY",
    # M
    "MANUAL", "MATCH", "MAXVALUE", "MEDIUMBLOB", "MEDIUMINT", "MEDIUMTEXT",
    "MIDDLEINT", "MINUTE_MICROSECOND", "MINUTE_SECOND", "MOD", "MODIFIES",
    # N
    "NATURAL", "NOT", "NO_WRITE_TO_BINLOG", "NTH_VALUE", "NTILE", "NULL",
    "NUMERIC",
    # O
    "OF", "ON", "OPTIMIZE", "OPTIMIZER_COSTS", "OPTION", "OPTIONALLY", "OR",
    "ORDER", "OUT", "OUTER", "OUTFILE", "OVER",
    # P
    "PARALLEL", "PARTITION", "PERCENT_RANK", "PRECISION", "PRIMARY",
    "PROCEDURE", "PURGE",
    # Q
    "QUALIFY",
    # R
    "RANGE", "RANK", "READ", "READS", "READ_WRITE", "REAL", "RECURSIVE",
    "REFERENCES", "REGEXP", "RELEASE", "RENAME", "REPEAT", "REPLACE",
    "REQUIRE", "RESIGNAL", "RESTRICT", "RETURN", "REVOKE", "RIGHT",
    "RLIKE", "ROW", "ROWS", "ROW_NUMBER",
    # S
    "SCHEMA", "SCHEMAS", "SELECT", "SENSITIVE", "SEPARATOR", "SET", "SHOW",
    "SIGNAL", "SMALLINT", "SPATIAL", "SPECIFIC", "SQL", "SQLEXCEPTION",
    "SQLSTATE", "SQLWARNING", "SQL_BIG_RESULT", "SQL_CALC_FOUND_ROWS",
    "SQL_SMALL_RESULT", "SSL", "STARTING", "STORED", "STRAIGHT_JOIN",
    "SYSTEM",
    # T
    "TABLE", "TABLESAMPLE", "TERMINATED", "THEN", "TINYBLOB", "TINYINT",
    "TINYTEXT", "TO", "TRAILING", "TRIGGER", "TRUE",
    # U
    "UNDO", "UNION", "UNIQUE", "UNLOCK", "UNSIGNED", "UPDATE", "USAGE",
    "USE", "USING", "UTC_DATE", "UTC_TIME", "UTC_TIMESTAMP",
    # V
    "VALUES", "VARBINARY", "VARCHAR", "VARCHARACTER", "VARYING", "VIRTUAL",
    # W
    "WHEN", "WHERE", "WHILE", "WINDOW", "WITH", "WRITE",
    # X
    "XOR",
    # Y
    "YEAR_MONTH",
    # Z
    "ZEROFILL",
})

# ---------------------------------------------------------------------------
# Keywords that are assigned their own dedicated token type by the classifier.
# All others in SQL_KEYWORDS receive the generic TT_KEYWORD type.
# ---------------------------------------------------------------------------

STRUCTURAL_KEYWORDS: frozenset[str] = frozenset({
    # DML verbs
    "SELECT", "INSERT", "UPDATE", "DELETE",
    # DDL verbs
    "DROP", "CREATE", "ALTER",
    # Clauses
    "FROM", "INTO", "WHERE", "SET", "VALUES",
    "ORDER", "BY", "ASC", "DESC",
    "GROUP", "HAVING", "LIMIT",
    # Joins
    "JOIN", "INNER", "LEFT", "RIGHT", "OUTER", "CROSS", "ON",
    # Logical
    "AND", "OR", "NOT", "IS", "IN", "LIKE", "BETWEEN", "NULL",
    # Object types
    "TABLE", "DATABASE",
    # Misc structural
    "AS", "DISTINCT",
})


def is_keyword(word: str) -> bool:
    """Return True if *word* (case-insensitive) is a SQL keyword."""
    return word.upper() in SQL_KEYWORDS


def is_structural_keyword(word: str) -> bool:
    """Return True if *word* is a keyword that gets its own token type."""
    return word.upper() in STRUCTURAL_KEYWORDS
