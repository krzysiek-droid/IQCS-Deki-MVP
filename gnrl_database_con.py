
import sys
import pandas as pd
import mariadb

with open(r"D:\CondaPy - Projects\PyGUIs\DekiApp_pyqt5\DekiResources\database_con.txt",
          'r', encoding="UTF-8") as f:
    db_credentials = f.read().split("\n")
    for i in range(len(db_credentials)):
        tmp = db_credentials[i].split(" = ")[1]
        db_credentials[i] = tmp

DATABASE_HOST = db_credentials[0]
DATABASE_USER = db_credentials[1]
DATABASE_PASSWORD = db_credentials[2]
DATABASE_NAME = db_credentials[3]
PORT = int(db_credentials[4])


def validate_text(text):
    tmp_text = text
    if text.isalnum():
        return text
    else:
        print(f"gnrl_database_con [validate_text]: {text} requires validation...", end='')
        for letter in text:
            if not letter.isalnum():
                tmp_text = tmp_text.replace(letter, '_')
        print(f"Validated text -> {tmp_text}")
        return tmp_text


class Database:

    def __init__(self):
        try:
            self.conn = mariadb.connect(
                user=DATABASE_USER,
                password=DATABASE_PASSWORD,
                host=DATABASE_HOST,
                port=PORT,
                database=DATABASE_NAME,
                connect_timeout=2
            )
        except mariadb.Error as e:
            print(f"Error connecting to MariaDB Platform via internet: {e}")
            try:
                self.conn = mariadb.connect(
                    user=DATABASE_USER,
                    password=DATABASE_PASSWORD,
                    host=f"192.168.1.103",
                    port=PORT,
                    database=DATABASE_NAME
                )
            except mariadb.Error as e:
                print(f"Error connecting to MariaDB Platform via LAN: {e}")
                sys.exit(1)

        self.cur = self.conn.cursor()
        self.cur.execute("SELECT version();")
        print(f'Database connection established, db version: {self.cur.fetchone()[0]}')

    def __del__(self):
        self.cur.close()
        self.conn.close()
        print(f'Database connection closed')

    def insert(self, table_name, values):
        # table_name = validate_text(table_name)
        print(f'Inserting into the database -> {table_name}', end='... ')
        try:
            db_columns = self.get_columns_names(table_name)
            placeholders = ','.join(["%s"] * len(db_columns))
            if type(values) == dict:
                values = [values.get(column, None) for column in db_columns]
            self.cur.execute(
                f"INSERT INTO {table_name} ({','.join(db_columns)})"
                f" VALUES ({placeholders})", values)
            print(f'Query executed.', end=' ')
        except ValueError:
            print(f'Values has to be inserted as a py list (not any other arrays!).')
        print(f"Committing the query...", end=' ')
        self.conn.commit()
        print('Committed.')

    def replace_row(self, table_name, replaced_row: dict, row_id=None):
        try:
            if row_id is None:
                row_id = int(list(replaced_row.values())[0])
            # Get the column names for the table
            columns = self.get_columns_names(table_name)
            # Remove the 'id' column from the list of column names
            columns.remove('id')
            # Construct the SET clause of the SQL query
            set_clause = ','.join([f'{col}=%s' for col in columns])
            # Append the row_id to the values list
            values = list(replaced_row.values())[1:]
            values.append(row_id)
            # Construct the SQL query with a WHERE clause that filters by id
            query = f"UPDATE {table_name} SET {set_clause} WHERE id = %s"
            # Execute the SQL query
            self.cur.execute(query, values)
        except ValueError:
            print(f'Values has to be inserted as a py list (not any other arrays!).')
        self.conn.commit()

    # returns a pandas DataFrame from given table and columns (as a list of strings)
    # returns all columns if given '*'
    def get_by_column(self, table_name, *columns):
        if len(columns) > 1:
            columns_txt = ','.join(columns)
        elif columns[0] == '*':
            columns_txt = columns[0]
            columns = self.get_columns_names(table_name)
            cols_names = []
            for name in columns:
                cols_names.append(name)
            columns = cols_names
        else:
            columns_txt = ''.join(columns)

        qry = f'SELECT {columns_txt} FROM {table_name}'
        self.cur.execute(qry)

        output_list = []
        minor_list = []
        for tuple_value in self.cur.fetchall():
            for value in tuple_value:
                minor_list.append(value)
            output_list.append(minor_list)
            minor_list = []

        df = pd.DataFrame(columns=columns)
        for record in output_list:
            series = pd.Series(record, index=columns)
            df = df.append(series, ignore_index=True)

        return df

    # Load data from xlsx file (excel) to given table
    def insertDB_from_xls(self, table_name, xls_path):
        df_ISO = pd.read_excel(xls_path)
        for index, row in df_ISO.iterrows():
            text_records = ','.join(map(str, row)).replace(" ", '')
            self.insert(table_name, text_records)
        self.table_into_DF(table_name)

    def insertDB_from_csv(self, table_name, csv_path, csv_separator):
        # table_name = validate_text(table_name)
        df = pd.read_csv(csv_path, sep=csv_separator)
        if self.is_table(table_name):
            print(f"Table {table_name} already exist. Inserting data....")
        else:
            self.create_table(table_name, df.columns.tolist())
            print(f"Table {table_name} created. Inserting data....")

        for index, row in df.iterrows():
            text_records = ','.join(map(str, row)).replace(" ", '')
            self.insert(table_name, text_records)

        self.table_into_DF(table_name)

    def delete_records(self, table_name, rowID):  # TODO: order by ID
        qry = f'DELETE FROM {table_name} WHILE id = %s'
        deleted_item = (rowID,)
        self.cur.execute(qry, deleted_item)
        self.conn.commit()
        print(f"Row {rowID} has been deleted from Database.")

    def table_into_DF(self, table_name):
        # self.reconnect()
        # table_name = validate_text(table_name)
        qry = f'SELECT * FROM {table_name}'
        self.cur.execute(qry)
        records = self.cur.fetchall()
        table_cols = self.get_columns_names(table_name)
        df = pd.DataFrame(columns=table_cols)
        for record in records:
            row_dict = {k: v for k, v in zip(table_cols, record)}
            x = pd.DataFrame.from_dict([row_dict])
            df = pd.concat([df, x])
        return df

    def get_row(self, table_name: str, col_name: str, row_pos: str):
        # table_name = validate_text(table_name)
        qry = f'SELECT * FROM {table_name} WHERE {col_name} = {row_pos}'
        self.cur.execute(qry)
        row_data = self.cur.fetchall()
        return row_data

    def get_columns_names(self, table_name):
        table_cols = f"SELECT column_name FROM information_schema.columns WHERE table_name='{table_name}' " \
                     f"ORDER BY ORDINAL_POSITION"
        self.cur.execute(table_cols)
        columns = []
        for column in self.cur.fetchall():
            columns.append(column[0])

        return columns

    def create_table(self, table_name, columns: list):
        columnList = []
        # table_name = validate_text(table_name)
        for columnName in columns:
            if not columnName.isalpha():
                # print(f"Wrong column name: {columnName}", end=", ")
                if columnName == ' ' or columnName == "id":
                    raise ValueError(f'Wrong column name: {columnName}')
                tmp_columnName = str(columnName)
                for letter in columnName:
                    if not letter.isalpha():
                        if letter == ".":
                            tmp_columnName = tmp_columnName.replace(letter, '')
                        tmp_columnName = tmp_columnName.replace(letter, '_')
                    #   print(f"Changed for: {tmp_columnName}")
                columnList.append(tmp_columnName + ' VARCHAR(200)')
                continue

            columnList.append(columnName + ' VARCHAR(200)')

        cols = ','.join([column for column in columnList])
        print(f"Proceeding table creation with columns: {cols}")
        if not self.is_table(table_name):
            id_column = columnList[0].split(' ')[0]
            qry = f"CREATE TABLE {table_name} ({cols}, PRIMARY KEY({id_column}))"
            self.cur.execute(qry)
            self.conn.commit()
            print(f"Table {table_name} has been created.")
        else:
            print(f"Table could not been created, because another table with the same name exists")
            return 0

    def create_table_2(self, table_name, columns: list, data=None):
        columnList = []
        # table_name = validate_text(table_name)
        for columnName in columns:
            if not columnName.isalpha():
                if columnName == ' ' or columnName == "id":
                    raise ValueError(f'Wrong column name: {columnName}')
                tmp_columnName = str(columnName)
                for letter in columnName:
                    if not letter.isalpha():
                        if letter == ".":
                            tmp_columnName = tmp_columnName.replace(letter, '')
                        tmp_columnName = tmp_columnName.replace(letter, '_')
                columnList.append(tmp_columnName + ' VARCHAR(200)')
                continue
            columnList.append(columnName + ' VARCHAR(200)')

        id_column = columnList[0].split(' ')[0]
        cols = ','.join([column for column in columnList[1::]])
        print(f"Proceeding table creation with columns: {cols}, and id column -> {id_column}")

        if self.is_table(table_name):
            print(f"Table already exists, dropping table {table_name}", end='... ')
            # If the table already exists, drop it
            qry = f"DROP TABLE {table_name}"
            self.cur.execute(qry)
            self.conn.commit()
            print(f"Table {table_name} has been dropped.")


        qry = f"CREATE TABLE {table_name} ({id_column} INT NOT NULL AUTO_INCREMENT, {cols}, PRIMARY KEY({id_column}))"
        self.cur.execute(qry)
        self.conn.commit()
        print(f"Table {table_name} has been created.")

        columns = self.get_columns_names(table_name)

        # If data is provided, insert into the newly created table
        if data is not None:
            try:
                placeholders = ','.join(["%s"] * len(columns))
                for i, row in data.iterrows():
                    values = row.values.tolist()
                    self.cur.execute(
                        f"INSERT INTO {table_name} ({','.join(columns)})"
                        f" VALUES ({placeholders})", values)
                    self.conn.commit()
                print(f"{len(data)} rows have been inserted into table {table_name}.")
            except Exception as exc:
                print(f"Failed to insert data into table {table_name}. Error: {exc}")
                self.conn.rollback()

    # searches if given table name exists in SQL server tables with table_schema=public
    # Boolean
    def is_table(self, table_name):
        table_name = validate_text(table_name)
        tables_list = self.show_tables(DATABASE_NAME)
        for table in tables_list:
            if table[0] == table_name.lower():
                return True
        print(f"gnrl_databse_con [func: is_table]: Table {table_name} not found in database. Tab list: {tables_list}")
        return False

    def show_tables(self, database_name):
        qry = f"SHOW TABLES FROM {database_name}"
        self.cur.execute(qry)
        return self.cur.fetchall()

    def add_column(self, table_name, column_name, data_type, values):
        qry = f"ALTER TABLE {table_name} ADD {column_name} {data_type}"
        self.cur.execute(qry)
        print(f"Column {column_name} has been added to table {table_name}")

    def check_records_number(self, table_name):
        self.cur.execute(f'SELECT * from {table_name}')
        records = self.cur.fetchall()
        if records is not None:
            return len(records)
        else:
            return 0

    def df_from_filteredTable(self, table_name, column_name, value, is_equal=True) -> pd.DataFrame:
        if is_equal:
            # print(f'Filtering the database table {table_name} for {value} in {column_name}')
            qry = f"SELECT * FROM {table_name} WHERE {column_name} = {value}  ORDER BY ID"
        else:
            # print(f'Filtering the database table {table_name} by {column_name} not equal != to {value}')
            qry = f"SELECT * FROM {table_name} WHERE {column_name} != {value}  ORDER BY ID"
        self.cur.execute(qry)
        records = self.cur.fetchall()
        table_cols = self.get_columns_names(table_name)
        df = pd.DataFrame(columns=table_cols)
        for record in records:
            row_dict = {k: v for k, v in zip(table_cols, record)}
            x = pd.DataFrame.from_dict([row_dict])
            df = pd.concat([df, x])
        return df

    def get_subConstruction_branch(self, root_id, table_name=None, df=None):
        if df is None:
            df = self.table_into_DF(table_name)
        # Find all rows with the given root_id as the parent_id

        children = df[df['parent_construction_id'] == root_id]
        # Base case: return the empty DataFrame if there are no children
        if children.empty:
            return pd.DataFrame()
        # Recursively find all children of each child
        result = pd.DataFrame()
        for index, child in children.iterrows():
            child_branch = self.get_subConstruction_branch(child['id'], table_name, df)
            if not child_branch.empty:
                result = pd.concat([result, child_branch])
        return pd.concat([children, result])

    def get_subConstruction_core(self, root_id, table_name=None, df=None) -> pd.DataFrame:
        if df is None:
            df = self.table_into_DF(table_name)

        # Find the row with the given root_id
        df = df.reset_index()
        root_row = df.iloc[[int(root_id) - 1]]
        if root_row.empty:
            return pd.DataFrame()

        # Find all parents of the root row
        parent_rows = pd.DataFrame(columns=df.columns)
        parent_id = root_row['parent_construction_id'].iloc[0]
        while parent_id is not None:
            parent_row = df.iloc[[int(parent_id) - 1]]
            if parent_row.empty:
                break
            parent_rows = pd.concat([parent_rows, parent_row])
            parent_id = parent_row['parent_construction_id'].iloc[0]
        return parent_rows

    def table_length(self, table_name):
        """
        Returns the number of rows in a table.
        Args:
            table_name (str): The name of the table to get the length of.
        Returns:
            An integer representing the number of rows in the table, or None if the table does not exist.
        """
        cursor = self.conn.cursor()
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        result = cursor.fetchone()
        if result:
            return result[0]
        else:
            return 0

    def rows_equal_count(self, table_name, column_name, value):
        """
        Returns the number of rows in a specified MariaDB database table
        where a given column has a specific value.

        Parameters:
        table_name (str): Name of the table to search.
        column_name (str): Name of the column to search for the value.
        value: Value to search for in the column.

        Returns:
        int: Number of rows in the table where the column has the specified value.
        """
        cursor = self.conn.cursor()
        query = f"SELECT COUNT(*) FROM {table_name} WHERE {column_name} = %s"
        cursor.execute(query, (value,))
        result = cursor.fetchone()
        return result[0]

    def reconnect(self):
        self.cur.close()
        self.conn.close()
        print(f"Database connection closed - trying to reconnect...")
        self.__init__()


if __name__ == "__main__":
    db = Database()
    # db_rows = db.df_from_filteredTable('deki_2022_SubConstructions', 'parent_construction_id', 1)
    # print(db_rows['id'].tolist())
    # for i in db_rows['id'].tolist():
    #     print(i)
    print(db)