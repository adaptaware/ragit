"""Exposes the functionality to simplify the interaction with the database."""

import psycopg2

import ragit.libs.common as common


def create_db_if_needed(db_name, schema=None):
    """Creates the database with the passed in name if it does not exist.

    :param str db_name: The name of the database to create.
    :param str schema: The db schema to use; if None it will be ignored.
    """
    assert len(db_name) <= 20, "Dbname is too long."
    try:
        conn_str = common.make_local_connection_string("postgres")
        SimpleSQL.register_connection_string(conn_str)
        with SimpleSQL() as db:
            # If the db already exists do nothing and exit.
            sql = _SQL_CHECK_DB_EXISTS.format(db_name=db_name)
            for row in db.execute_query(sql):
                counter = row[0]
                if counter == 1:
                    return

            # The db does not exist, create it and exit.
            sql = _SQL_CREATE_DB.format(db_name=db_name)
            db.execute_non_query(sql)

        # Create the schema if it was passed.
        if schema:
            conn_str = common.make_local_connection_string(db_name)
            SimpleSQL.register_connection_string(conn_str)
            with SimpleSQL() as db:
                db.execute_non_query(schema)
    finally:
        SimpleSQL.register_connection_string(None)


def delete_db_if_exists(db_name):
    """Deletes the passed in database if it exists.

    :param str db_name: The name of the database to delete.
    """
    assert len(db_name) <= 20, "Dbname is too long."
    try:
        conn_str = common.make_local_connection_string("postgres")
        SimpleSQL.register_connection_string(conn_str)
        with SimpleSQL() as db:
            # If the db does not already exist do nothing and exit.
            sql = _SQL_CHECK_DB_EXISTS.format(db_name=db_name)
            for row in db.execute_query(sql):
                counter = row[0]
                if counter == 0:
                    return

            # The db does not exist, create it and exit.
            sql = _SQL_DELETE_DB.format(db_name=db_name)
            db.execute_non_query(sql)
    finally:
        SimpleSQL.register_connection_string(None)


class SimpleSQL:
    """Provides a simplified interface for interacting with PostgreSQL."""

    _connection_string = None

    @classmethod
    def register_connection_string(cls, connection_string):
        """Registers the connection string for subsequent database interactions.

        :param connection_string: The connection string to the database.
        """
        cls._connection_string = connection_string

    def __enter__(self):
        """Establishes a database connection when entering a with block.

        : return: The SimpleSQL instance itself.

        :raises psycopg2.DatabaseError: If an error occurs during execution.
        """
        self._connection = psycopg2.connect(self._connection_string)
        self._connection.autocommit = True
        return self

    def __exit__(self, exc_type, exc_value, trace):
        """Closes the database connection when exiting a with block.

        :param exc_type: The exception type.
        :param exc_value: The exception value.
        :param trace: The exception traceback.
        """
        assert self._connection
        self._connection.close()
        self._connection = None

    def execute_query(self, sql):
        """Executes a query and yields the results row by row.

        :param sql: The SQL SELECT statement to execute.

        :yield: A tuple representing each row of the query result.

        :raises psycopg2.DatabaseError: If an error occurs during execution.
        """
        assert self._connection
        with self._connection.cursor() as cursor:
            cursor.execute(sql)
            records = cursor.fetchall()
            for row in records:
                yield row

    def execute_non_query(self, sql):
        """Executes a non select statement.

        :param sql: the sql to execute

        :raise:psycopg2.DatabaseError
        """
        assert self._connection
        with self._connection.cursor() as cursor:
            cursor.execute(sql)


# Whatever follows this line is private to the module and should not be
# used from the outside.

_SQL_CHECK_DB_EXISTS = """ 
SELECT count(*) FROM pg_database WHERE datname = '{db_name}' 
"""

_SQL_CREATE_DB = """CREATE DATABASE {db_name} """

_SQL_DELETE_DB = """DROP DATABASE {db_name}"""
