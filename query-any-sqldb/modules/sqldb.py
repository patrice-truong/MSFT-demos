import pymssql

class AzureSQLDatabase:
    def __init__(self, server, database, username, password):
        self.connection = None
        self.cursor = None
        self.server = server
        self.database = database
        self.username = username
        self.password = password

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.disconnect()

    def connect(self):
        try:
            self.connection = pymssql.connect(
                server=self.server,
                database=self.database,
                user=self.username,
                password=self.password
            )
            self.cursor = self.connection.cursor()
            return "OK"
        except Exception as e:
            return f"Exception connecting to the database: {str(e)}"

    def disconnect(self):
        if self.connection:
            self.connection.close()
            print("Disconnected from the database.")

    # Modify other methods accordingly based on the differences in API between pymssql and pyodbc
    # For example, the parameter placeholder in pymssql is '%s' instead of '?'

    def upsert(self, table_name, _dict, schema='dbo'):
        try:
            existing_record = self.get(table_name, _dict.get('id'), schema=schema)

            if existing_record:
                update_query = f"UPDATE {schema}.{table_name} SET "
                update_query += ", ".join([f"{key} = %s" for key in _dict.keys() if key != 'id'])
                update_query += f" WHERE id = {_dict['id']}"
                self.cursor.execute(update_query, tuple(_dict[key] for key in _dict.keys() if key != 'id'))
            else:
                insert_query = f"INSERT INTO {schema}.{table_name} ({', '.join(_dict.keys())}) VALUES ({', '.join(['%s'] * len(_dict))})"
                self.cursor.execute(insert_query, tuple(_dict.values()))

            self.connection.commit()
            print("Upsert operation successful.")
        except Exception as e:
            print(f"Exception during upsert operation: {str(e)}")

    def delete(self, table_name, _id, schema='dbo'):
        try:
            delete_query = f"DELETE FROM {schema}.{table_name} WHERE id = %s"
            self.cursor.execute(delete_query, (_id,))
            self.connection.commit()
            print("Delete operation successful.")
        except Exception as e:
            print(f"Exception during delete operation: {str(e)}")

    def get(self, table_name, _id, schema='dbo'):
        try:
            select_query = f"SELECT * FROM {schema}.{table_name} WHERE id = ?"
            self.cursor.execute(select_query, (_id,))
            row = self.cursor.fetchone()
            return dict(zip([column[0] for column in self.cursor.description], row)) if row else None
        except Exception as e:
            print(f"Exception during get operation: {str(e)}")
            return None

    def get_all(self, table_name, schema='dbo'):
        try:
            select_all_query = f"SELECT * FROM {schema}.{table_name}"
            self.cursor.execute(select_all_query)
            rows = self.cursor.fetchall()
            columns = [column[0] for column in self.cursor.description]
            return [dict(zip(columns, row)) for row in rows]
        except Exception as e:
            print(f"Exception during get_all operation: {str(e)}")
            return []

    def run_sql(self, sql):
        try:
            self.cursor.execute(sql)
            rows = self.cursor.fetchall()
            columns = [column[0] for column in self.cursor.description]
            return [dict(zip(columns, row)) for row in rows]
        except Exception as e:
            print(f"Exception during SQL statement execution: {str(e)}")
            return []

    def get_table_definition(self, schema, table_name):
        try:
            query = f"SELECT COLUMN_NAME, DATA_TYPE, CHARACTER_MAXIMUM_LENGTH FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = '{table_name}' AND TABLE_SCHEMA = '{schema}'"
            self.cursor.execute(query)
            columns = self.cursor.fetchall()
            definition = [f"{col[0]} {col[1]}({col[2]})" if col[2] else f"{col[0]} {col[1]}" for col in columns]
            return f"""
            CREATE TABLE {schema}.{table_name} (
                {', '.join(definition)});
                """
        except Exception as e:
            print(f"Exception getting table definition: {str(e)}")
            return ""

    def get_all_table_names(self):
        try:
            query = "SELECT TABLE_SCHEMA, TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE'"
            self.cursor.execute(query)
            return [(row[0], row[1]) for row in self.cursor.fetchall()]
        except Exception as e:
            print(f"Exception getting table names: {str(e)}")
            return []

    def get_table_definitions_for_prompt(self):
        table_definitions = []
        table_names_with_schema = self.get_all_table_names()

        for schema, table_name in table_names_with_schema:
            table_definition = self.get_table_definition(schema, table_name)
            table_definitions.append(table_definition)

        return "\n".join(table_definitions)

