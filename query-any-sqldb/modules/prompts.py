SQL_TABLE_DEFINITIONS_CAP_REF = "TABLE_DEFINITIONS"
RESPONSE_FORMAT_CAP_REF =  "RESPONSE_FORMAT"
SQL_DELIMITER = "---"

SQL_TABLE_DEFINITIONS_CAP_REF_PROMPT = f"""
\nUsing the T-SQL dialect, generate the SQL query required to answer the question above. 
- You can only use the tables described in the {SQL_TABLE_DEFINITIONS_CAP_REF}.
- You must *ABSOLUTELY* use T-SQL syntax. If the generated can not executed on a SQL Server, rewrite it.
- Validate all fields in the query to make sure they exist in the tabes described in the {SQL_TABLE_DEFINITIONS_CAP_REF}.
"""

RESPONSE_FORMAT_CAP_REF_PROMPT = f"""
Respond in this format {RESPONSE_FORMAT_CAP_REF}. 
- All observations should be placed above {SQL_DELIMITER}.
- Replace the text between <> with the appropriate content.
"""
